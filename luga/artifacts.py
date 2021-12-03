from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple, Union
import httpx
from fasttext import FastText, load_model  # type: ignore
from numpy import array
from numpy.typing import NDArray


__MODEL_PATH = Path(__file__).parent / "models"
__MODEL_FILE = __MODEL_PATH / "language.bin"  # lid.176.bim 128MB model
__MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"


def model_loader(*, model_url: str, re_download: Optional[bool] = False) -> None:
    """Model Downloader

    Args:
        model_url (str): url link to fasttext language model
        re_download (bool, optional): overides a downloaded model. Defaults to False.
    Returns:
        None
    """

    if not __MODEL_FILE.exists() or re_download:
        # print(f"Downloading language model from {__MODEL_URL!r}. Runs only once!")
        __MODEL_PATH.mkdir(exist_ok=True)

        timeout = httpx.Timeout(10.0, connect=60.0)
        with httpx.Client(timeout=timeout) as client, __MODEL_FILE.open(
            "wb"
        ) as f_model:
            model_content = client.get(model_url)
            f_model.write(model_content.content)
        # print("Downloading completed!")


def model_deleter(*, model_file: Path = __MODEL_FILE) -> bool:
    """Model Remover

    Args:
        model_file (Path, optional): path to where the model is.
        Defaults to __MODEL_FILE.

    Returns:
        bool: True if deletion was successful, else False
    """

    if not model_file.exists():
        return False

    model_file.unlink()
    return True


@dataclass(frozen=True)
class Language:
    name: str = field(default="unknown", metadata={"language": "predicted language"})
    score: float = field(
        default=0.0, metadata={"trustability": "probability of prediction"}
    )

    @staticmethod
    def keys() -> List[str]:
        return ["name", "score"]

    def __getitem__(self, key: str) -> Union[Any, str, float]:
        item = {"name": self.name, "score": self.score}

        return item.get(key)


def beautify_one(
    response: Tuple[str, NDArray], threshold: Optional[float] = 0.5
) -> Language:

    score_: NDArray
    language, score_ = response
    # (('__label__da',), array([0.99840873]))
    score = score_.squeeze().item()

    if score < threshold:
        return Language()

    return Language(name=language[0].replace("__label__", ""), score=score)


def beautify_many(
    responses: Tuple[str, NDArray],
    threshold: Optional[float] = 0.5,
    only_language: Optional[bool] = False,
    to_array: Optional[bool] = False,
) -> Union[List[str], List[Language], NDArray]:

    # ([['__label__da'], ['__label__en']],
    # [array([0.99840873], dtype=float32), array([0.9827167], dtype=float32)])

    languages, scores = responses
    results_ = []
    for lang, score_ in zip(languages, scores):
        score = score_.squeeze().item()

        if score < threshold:
            results_.append(Language())

        else:
            results_.append(
                Language(name=lang[0].replace("__label__", ""), score=score)
            )

    if only_language:
        results = [response.name for response in results_]

    if to_array:
        results = array(results)

    return results


# mute warning with eprint
# Warning : `load_model` does not return WordVectorModel or SupervisedModel
#  any more, but a `FastText` object which is very similar.
# pylint: disable=E1111
FastText.eprint = lambda x: None
model_loader(model_url=__MODEL_URL)
fmodel = load_model(f"{__MODEL_FILE}")
