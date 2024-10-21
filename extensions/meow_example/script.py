import torch
from transformers import LogitsProcessor

from modules import shared

meow_processor = None


class MeowLogitsProcessor(LogitsProcessor):
    '''
    Fixes the logits to only return meowing...
    '''
    def __init__(self):
        self.target_token = 0  # Token index to look up at each step.
        self.limited_response = "Meow meow MEOW! Meow."
        # Tokenize and strip off the 'beginning of' token.
        self.sample_ids = shared.tokenizer(self.limited_response, return_tensors="pt").input_ids[:, 1:]
        # Add the 'End of' token. This is gross, but it's how torch works...
        eos = torch.tensor([shared.tokenizer.eos_token_id])
        self.sample_ids = torch.cat((self.sample_ids, eos.unsqueeze(0)), dim=1)

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        # Nuke all the scores in-place.
        scores.fill_(-float("Inf"))

        current_token_index = self.target_token % self.sample_ids.size(1)
        current_token_id = self.sample_ids[0][current_token_index]

        # Set the score of the current token to 1; since everything else is -Infinity, it will be picked.
        scores.index_fill_(1, torch.tensor([current_token_id]), float(1))
        # If, instead, you wanted it to pick randomly from all the tokens allowed in `self.sample_ids`:
        #   scores.index_fill_(1, self.sample_ids[0], float(1))
        # It's less cogent, but it's also fun.
        self.target_token += 1

        return scores


def setup():
    global meow_processor
    meow_processor = MeowLogitsProcessor()


def logits_modifier(input_ids: torch.LongTensor, logits: torch.FloatTensor) -> torch.FloatTensor:
    global meow_processor

    return meow_processor(input_ids, logits)
