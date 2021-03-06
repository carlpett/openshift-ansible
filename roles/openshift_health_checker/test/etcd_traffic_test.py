import pytest

from openshift_checks.etcd_traffic import EtcdTraffic


@pytest.mark.parametrize('group_names,version,is_active', [
    (['masters'], "3.5", False),
    (['masters'], "3.6", False),
    (['nodes'], "3.4", False),
    (['etcd'], "3.4", True),
    (['etcd'], "3.5", True),
    (['etcd'], "3.1", False),
    (['masters', 'nodes'], "3.5", False),
    (['masters', 'etcd'], "3.5", True),
    ([], "3.4", False),
])
def test_is_active(group_names, version, is_active):
    task_vars = dict(
        group_names=group_names,
        openshift=dict(
            common=dict(short_version=version),
        ),
    )
    assert EtcdTraffic(task_vars=task_vars).is_active() == is_active


@pytest.mark.parametrize('group_names,matched,failed,extra_words', [
    (["masters"], True, True, ["Higher than normal", "traffic"]),
    (["masters", "etcd"], False, False, []),
    (["etcd"], False, False, []),
])
def test_log_matches_high_traffic_msg(group_names, matched, failed, extra_words):
    def execute_module(module_name, *_):
        return {
            "matched": matched,
            "failed": failed,
        }

    task_vars = dict(
        group_names=group_names,
        openshift=dict(
            common=dict(service_type="origin", is_containerized=False),
        )
    )

    result = EtcdTraffic(execute_module, task_vars).run()

    for word in extra_words:
        assert word in result.get("msg", "")

    assert result.get("failed", False) == failed


@pytest.mark.parametrize('is_containerized,expected_unit_value', [
    (False, "etcd"),
    (True, "etcd_container"),
])
def test_systemd_unit_matches_deployment_type(is_containerized, expected_unit_value):
    task_vars = dict(
        openshift=dict(
            common=dict(is_containerized=is_containerized),
        )
    )

    def execute_module(module_name, args, *_):
        assert module_name == "search_journalctl"
        matchers = args["log_matchers"]

        for matcher in matchers:
            assert matcher["unit"] == expected_unit_value

        return {"failed": False}

    EtcdTraffic(execute_module, task_vars).run()
