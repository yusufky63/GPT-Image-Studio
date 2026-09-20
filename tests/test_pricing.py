from app.pricing import calculate_cost
def test_cost():
    u={"input_tokens_details":{"text_tokens":1000,"image_tokens":2000},"output_tokens":3000}
    assert abs(calculate_cost("gpt-image-2.5-sunburst",u)-0.111) < 1e-9
