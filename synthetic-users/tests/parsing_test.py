from api.llm_api import LLM_API
from core.names import increment_trailing_number
from modelfile import system


def test_llm_parsing():
    llm_api = LLM_API("lamma3.2:latest", system)
    assert isinstance(
        llm_api.parse_response('{"answer": 1.0, "response_time": 1.0}'), dict
    )
    assert isinstance(
        llm_api.parse_response('{"answer": "1.0", "response_time": 1.0}'), dict
    )

    assert (
        llm_api.parse_response('{"answer": 1.0, "response_time": 1.0, "another": 1}')
        is None
    )

    assert llm_api.parse_response('{"answer": nan, "response_time": 1.0}') is None
    assert llm_api.parse_response('{"answer": "d", "response_time": 1.0}') is None
    # assert llm_api.parse_llm_response('{"answer": false, "response_time": 1.0}') is None # false is 0
    assert llm_api.parse_response('{"answer": [], "response_time": 1.0}') is None

    assert llm_api.parse_response('{"answer": inf, "response_time": 1.0}') is None
    assert llm_api.parse_response('{"answer": -inf, "response_time": 1.0}') is None
    assert llm_api.parse_response('{"answer": 1.0, "response_time": nan}') is None
    assert llm_api.parse_response('{"answer": 1.0, "response_time": inf}') is None
    assert llm_api.parse_response('{"answer": 1.0, "response_time": -inf}') is None
    assert llm_api.parse_response('{"answer": 1e500, "response_time": 1.0}') is None

    assert llm_api.parse_response('{"answer": 1.0}') is None
    assert llm_api.parse_response('{"response_time": 1.0}') is None
    assert llm_api.parse_response("arsotanrostnariosntoinarst") is None


def test_increment_trailing_number():
    assert increment_trailing_number("test") == "test1"
    assert increment_trailing_number("test1") == "test2"
    assert increment_trailing_number("test9") == "test10"
    assert increment_trailing_number("test10") == "test11"
    assert increment_trailing_number("test9999") == "test10000"
    assert increment_trailing_number("test10000") == "test10001"
