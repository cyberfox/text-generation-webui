from transformers import (GPT2Tokenizer, AutoModelForCausalLM,
                          GPTNeoXForCausalLM, AutoTokenizer)
import numpy as np
import torch
from transformers import (LogitsProcessor, LogitsProcessorList,
                          MinLengthLogitsProcessor, TemperatureLogitsWarper,
                          TopKLogitsWarper, TopPLogitsWarper,
                          TypicalLogitsWarper)
from transformers.generation import LogitNormalization
import torch.nn.functional as F


class CFGLogits(LogitsProcessor):
    r"""Logits processor for Classifier-Free Guidance (CFG). The processors
    computes a weighted average across scores from prompt conditional and prompt unconditional (or negative) logits,
    parameterized by the `guidance_scale`. The unconditional scores are computed internally by prompting `model` with
    the `uncond` branch. Finally, according to CFG Rescale, the reweighted logits are interpolated back with weight
    `rescale_factor` the conditional ones to smooth the effect and increase output quality.

    See [the paper](https://arxiv.org/abs/2306.17806) for more information.

    Args:
        guidance_scale (float):
            The guidance scale for classifier free guidance (CFG). CFG is enabled by setting `guidance_scale > 1`.
            Higher guidance scale encourages the model to generate samples that are more closely linked to the input
            prompt, usually at the expense of poorer quality.
        uncond (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
            Indices of input sequence tokens in the vocabulary for the unconditional branch.
        model:
            The LM computing the unconditional scores. Supposedly the same as the one computing the conditional scores.
            Both models must use the same tokenizer.
        smooth_factor (float):
            The interpolation weight for CFG Rescale. 1 means no rescaling, 0 reduces to the conditional scores without
            CFG. Turn it lower if the output degenerates. Lower values allow for higher guidance scale.
    """

    def __init__(self, guidance_scale, uncond, model, rescale_factor=1.0):
        self.guidance_scale = guidance_scale
        self.uncond = uncond
        self.model = model
        self.out = None
        self.rescale_factor = rescale_factor

    def __call__(self, input_ids, scores):
        scores = F.log_softmax(scores, dim=-1)
        if self.guidance_scale == 1:
            return scores

        if self.out is None:
            self.out = self.model(self.uncond)
        else:
            self.out = self.model(input_ids[:, -1:], past_key_values=self.out.past_key_values)
        unconditional_logits = F.log_softmax(self.out.logits[0][-1:], dim=-1)
        out = self.guidance_scale * (scores - unconditional_logits) + unconditional_logits
        out = F.log_softmax(out, dim=-1)
        if self.rescale_factor == 1:
            return out
        return self.rescale_factor * out + (1 - self.rescale_factor) * scores


# paper usage: (copying and editing @grantCelley 's answer)
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import LogitsProcessorList, TemperatureLogitsWarper, TopPLogitsWarper

print("Getting the tokenizer.")
tokenizer = AutoTokenizer.from_pretrained("models/openlm-research_open_llama_3b")

print("Loading the model.")
model = AutoModelForCausalLM.from_pretrained("models/openlm-research_open_llama_3b")

prompt = tokenizer("Today a dragon flew over Paris, France,", return_tensors='pt')
# either provide a negative prompt:
neg_prompt = tokenizer("A sad event happened,", return_tensors='pt')['input_ids']
# or don't:
# neg_prompt = prompt['input_ids'][:, -1:]

# device = 'cuda:0'
device = 'cpu'
print("Calling model.to()")
model.to(device)
print("Calling model.generate.")
outputs = model.generate(
    input_ids=prompt['input_ids'].to(device),
    attention_mask=prompt['attention_mask'].to(device),
    max_new_tokens=125,
    logits_processor=LogitsProcessorList([
        # inputs_cfg usually is the last token of the prompt but there are
        # possibilities of negative prompting that are explored in the paper
        CFGLogits(1.5, neg_prompt.to(device), model),
        TemperatureLogitsWarper(0.8),
        TopPLogitsWarper(0.95),
    ]),
    do_sample=True,
)

print(tokenizer.decode(outputs[0]))