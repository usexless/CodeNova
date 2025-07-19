import os
from agents.tool_agent import ToolAgent


def test_deployment_config(tmp_path):
    config_file = tmp_path / "deploy.json"
    config_file.write_text('{"name": "test"}')
    agent = ToolAgent()
    result = agent.read_deployment_config(str(config_file))
    assert result["status"] == "success"
    assert result["config"]["name"] == "test"


def test_deploy_web_app():
    agent = ToolAgent()
    result = agent.deploy_web_app("./", platform="test")
    assert result["status"] == "success"


def test_check_deploy_status():
    agent = ToolAgent()
    result = agent.check_deploy_status("123")
    assert result["status"] == "success"


def test_browser_preview(tmp_path):
    dir_path = tmp_path
    (dir_path / "index.html").write_text("<h1>test</h1>")
    agent = ToolAgent()
    result = agent.browser_preview(str(dir_path), port=0)
    assert result["status"] == "success"

