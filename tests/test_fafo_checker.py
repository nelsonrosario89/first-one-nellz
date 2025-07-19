"""Unit tests for fafo_checker using moto to mock IAM."""
import sys
from importlib import reload

import boto3
import pytest
from moto import mock_iam

# Import path fix – ensures scripts package is discoverable when running pytest from repo root
sys.path.append("scripts")

import scripts.fafo_checker as fafo_checker  # noqa: E402  pylint: disable=import-error


@mock_iam
def test_exit_code_when_all_users_have_mfa(monkeypatch):
    """fafo_checker should exit 0 when every IAM user has at least one MFA device."""
    iam = boto3.client("iam", region_name="us-east-1")

    # Create user and virtual MFA device
    iam.create_user(UserName="alice")
    iam.create_virtual_mfa_device(VirtualMfaDeviceName="alice-mfa")
    iam.enable_mfa_device(
        UserName="alice",
        SerialNumber="arn:aws:iam::123456789012:mfa/alice-mfa",
        AuthenticationCode1="123456",
        AuthenticationCode2="654321",
    )

    with pytest.raises(SystemExit) as exc:
        reload(fafo_checker)
    assert exc.value.code == 0


@mock_iam
def test_exit_code_when_user_without_mfa(monkeypatch):
    """fafo_checker should exit 2 when at least one user lacks MFA."""
    iam = boto3.client("iam", region_name="us-east-1")

    # Create user without MFA
    iam.create_user(UserName="bob")

    with pytest.raises(SystemExit) as exc:
        reload(fafo_checker)
    assert exc.value.code == 2
