import torch

from modules import shared

inverted_vocab_dict = None
removed_token = None


def setup():
    global inverted_vocab_dict
    inverted_vocab_dict = {v: k for k, v in shared.tokenizer.get_vocab().items()}


def tokenizer_modifier(state, prompt, input_ids, input_embeds):
    global removed_token
    removed_token = input_ids[:, -1].item()
    removed_token_string = shared.tokenizer.decode([removed_token], add_special_tokens=False)
    # If it's the end-of-sequence token, leave it alone.
    if removed_token == shared.tokenizer.eos_token_id:
        removed_token = None
        return prompt, input_ids, input_embeds
    if prompt.endswith(removed_token_string):
        prompt = prompt[:-len(removed_token_string)]
    return prompt, input_ids[:, :-1], input_embeds


def logits_modifier(input_ids: torch.LongTensor, logits: torch.FloatTensor) -> torch.FloatTensor:
    global removed_token, inverted_vocab_dict

    if removed_token is not None:
        vocab_dict = shared.tokenizer.get_vocab()
        removed_token_str = inverted_vocab_dict[removed_token]
        filtered_token_ids = [vocab_dict[token] for token in vocab_dict if not token.startswith(removed_token_str)]
        tensor_token_ids = torch.tensor(filtered_token_ids)
        logits.index_fill_(1, tensor_token_ids, -float("Inf"))
        removed_token = None

    return logits
