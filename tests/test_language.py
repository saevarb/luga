from luga import language

# use parameterize with different languages


def test_sentence():

    response = language("this is just a simple test")

    assert response.name == "en", "language detection failed"
    assert response.score > 0.5, "score went boom!"
