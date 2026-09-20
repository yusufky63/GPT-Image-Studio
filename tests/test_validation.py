import pytest
from app.validation import validate_size,validate_options
@pytest.mark.parametrize("s,expected",[("3840x2160",(3840,2160)),("2160x3840",(2160,3840)),("2048x2048",(2048,2048)),("3360x1440",(3360,1440))])
def test_valid(s,expected):assert validate_size(s)==expected
@pytest.mark.parametrize("s",["3839x2160","4000x2000","100x100","3840x128","4096x2048"])
def test_invalid(s):
    with pytest.raises(ValueError):validate_size(s)
def test_quality():
    with pytest.raises(ValueError):validate_options("gpt-image-2","max","png")
