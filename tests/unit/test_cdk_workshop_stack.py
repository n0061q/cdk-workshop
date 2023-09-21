import pytest
from aws_cdk import Stack, aws_lambda as _lambda, assertions

from cdk_workshop.hitcounter import HitCounter


@pytest.fixture
def stack():
    yield Stack()


@pytest.fixture
def downstream_lambda(stack):
    yield _lambda.Function(
        stack,
        "TestFunction",
        runtime=_lambda.Runtime.PYTHON_3_7,
        handler="hello.handler",
        code=_lambda.Code.from_asset("lambda"),
    )


@pytest.fixture
def hc(stack, downstream_lambda):
    yield HitCounter(stack, "HitCounter", downstream=downstream_lambda)


@pytest.fixture
def hc_template(hc, stack):
    yield assertions.Template.from_stack(stack)


def test_hitcounter_ddb_table_created(hc_template):
    hc_template.resource_count_is("AWS::DynamoDB::Table", 1)


def test_hitcounter_lambda_has_env_vars(hc_template):
    envCapture = assertions.Capture()

    hc_template.has_resource_properties(
        "AWS::Lambda::Function",
        {
            "Handler": "hitcount.handler",
            "Environment": envCapture,
        },
    )

    assert envCapture.as_object() == {
        "Variables": {
            "DOWNSTREAM_FUNCTION_NAME": {"Ref": "TestFunction22AD90FC"},
            "HITS_TABLE_NAME": {"Ref": "HitCounterHits079767E5"},
        },
    }


@pytest.mark.skip("TBD")
def test_hitcounter_ddb_with_encryption(hc_template):
    hc_template.has_resource_properties(
        "AWS::DynamoDB::Table",
        {
            "SSESpecification": {
                "SSEEnabled": True,
            },
        },
    )


@pytest.mark.parametrize("read_capacity", (1, 4, 21, 50, 100))
def test_hitcounter_ddb_read_capacity_range(stack, downstream_lambda, read_capacity):
    with pytest.raises(ValueError):
        HitCounter(stack, "HitCounter", downstream=downstream_lambda, read_capacity=read_capacity)
