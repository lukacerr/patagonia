"""Registro central de tools disponibles para planner y executor."""

from typing import cast

from langchain_core.tools import BaseTool

from app.tools.add_firewall_rule import add_firewall_rule
from app.tools.add_user_to_security_group import add_user_to_security_group
from app.tools.apply_terraform_plan import apply_terraform_plan
from app.tools.configure_autoscaling import configure_autoscaling
from app.tools.create_dns_record import create_dns_record
from app.tools.create_kubernetes_namespace import create_kubernetes_namespace
from app.tools.create_load_balancer import create_load_balancer
from app.tools.create_log_retention_policy import create_log_retention_policy
from app.tools.create_monitoring_alert import create_monitoring_alert
from app.tools.create_postgres_database import create_postgres_database
from app.tools.create_redis_cache import create_redis_cache
from app.tools.create_s3_bucket import create_s3_bucket
from app.tools.create_service_account import create_service_account
from app.tools.deploy_container_service import deploy_container_service
from app.tools.enable_vpn_access import enable_vpn_access
from app.tools.grant_iam_role import grant_iam_role
from app.tools.purge_cdn_cache import purge_cdn_cache
from app.tools.restart_service import restart_service
from app.tools.restore_database_backup import restore_database_backup
from app.tools.rotate_secret import rotate_secret
from app.tools.run_database_backup import run_database_backup
from app.tools.run_health_check import run_health_check
from app.tools.scale_kubernetes_deployment import scale_kubernetes_deployment
from app.tools.update_container_image import update_container_image
from app.tools.validate_resource_exists import validate_resource_exists

all_tools: list[BaseTool] = [
    create_s3_bucket,
    create_postgres_database,
    enable_vpn_access,
    add_user_to_security_group,
    add_firewall_rule,
    validate_resource_exists,
    create_redis_cache,
    create_kubernetes_namespace,
    deploy_container_service,
    configure_autoscaling,
    create_load_balancer,
    create_dns_record,
    purge_cdn_cache,
    rotate_secret,
    create_service_account,
    grant_iam_role,
    create_monitoring_alert,
    create_log_retention_policy,
    run_database_backup,
    restore_database_backup,
    scale_kubernetes_deployment,
    restart_service,
    run_health_check,
    apply_terraform_plan,
    update_container_image,
]


def _tool_args_schema(tool: BaseTool) -> dict[str, object]:
    """Devuelve el schema JSON de argumentos para documentar capacidades."""

    schema = tool.args_schema
    if schema is None:
        return {}

    if isinstance(schema, dict):
        return cast(dict[str, object], schema)

    return cast(dict[str, object], schema.model_json_schema())


tool_metadata: list[dict[str, object]] = [
    {
        "name": tool.name,
        "description": tool.description,
        "args_schema": _tool_args_schema(tool),
    }
    for tool in all_tools
]

__all__ = ["all_tools", "tool_metadata"]
