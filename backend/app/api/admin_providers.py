from html import escape
from urllib.parse import quote, urlencode

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.admin_auth import verify_admin_token
from app.repositories.model_config_repository import (
    create_config,
    delete_config,
    get_config,
    list_configs,
    update_config,
)
from app.schemas.model_config import ModelConfigCreate, ModelConfigUpdate
from app.services.provider_test_service import test_provider_config


router = APIRouter(tags=["admin-provider-webui"])


@router.get("/admin/providers", response_class=HTMLResponse)
def provider_admin_page(
    token: str | None = None,
    test_status: str | None = None,
    test_message: str | None = None,
) -> str:
    if not _is_valid_token(token):
        return _page(
            title="管理员登录",
            body="""
            <section class="panel narrow">
              <p class="eyebrow">Provider Admin</p>
              <h1>模型配置后台</h1>
              <p>请输入后端管理员令牌。令牌来自环境变量 <code>ADMIN_WEBUI_TOKEN</code>。</p>
              <form method="get" action="/admin/providers">
                <label>管理员令牌<input name="token" type="password" autocomplete="off" required></label>
                <button type="submit">进入配置</button>
              </form>
            </section>
            """,
        )

    configs = list_configs(user_id=None)
    rows = "\n".join(_render_config_card(config, token or "") for config in configs)
    if not rows:
        rows = '<p class="empty">暂无全局模型配置。请先新增通用模型。</p>'
    notice = _render_notice(test_status, test_message)

    return _page(
        title="模型配置后台",
        body=f"""
        <header class="topbar">
          <div>
            <p class="eyebrow">Global Provider Admin</p>
            <h1>后端模型配置</h1>
            <p>这里配置平台统一承担的通用大模型 API。普通用户前端不会看到 API Key 或 Base URL。</p>
          </div>
          <a class="ghost" href="/docs">API 文档</a>
        </header>
        <main class="layout">
          <section class="panel">
            <h2>新增 Provider</h2>
            {_render_form(token or "")}
          </section>
          <section class="panel">
            <h2>当前全局配置</h2>
            {notice}
            <div class="list">{rows}</div>
          </section>
        </main>
        """,
    )


@router.post("/admin/providers/save")
def save_provider(
    token: str = Form(...),
    provider_name: str = Form(...),
    provider_type: str = Form(...),
    base_url: str = Form(...),
    model_name: str = Form(...),
    api_key: str = Form(default=""),
    enabled: str | None = Form(default=None),
    config_id: int | None = Form(default=None),
) -> RedirectResponse:
    verify_admin_token(token)
    is_enabled = enabled == "on"

    if config_id:
        payload = {
            "provider_name": provider_name.strip(),
            "provider_type": provider_type,
            "base_url": base_url.strip().rstrip("/"),
            "model_name": model_name.strip(),
            "enabled": is_enabled,
        }
        if api_key.strip():
            payload["api_key"] = api_key.strip()
        update_config(config_id, ModelConfigUpdate(**payload), user_id=None)
    else:
        create_config(
            ModelConfigCreate(
                provider_name=provider_name.strip(),
                provider_type=provider_type,
                base_url=base_url.strip().rstrip("/"),
                api_key=api_key.strip(),
                model_name=model_name.strip(),
                enabled=is_enabled,
            ),
            user_id=None,
        )

    return RedirectResponse(url=f"/admin/providers?token={quote(token)}", status_code=303)


@router.post("/admin/providers/delete")
def remove_provider(
    token: str = Form(...),
    config_id: int = Form(...),
) -> RedirectResponse:
    verify_admin_token(token)
    delete_config(config_id, user_id=None)
    return RedirectResponse(url=f"/admin/providers?token={quote(token)}", status_code=303)


@router.post("/admin/providers/test")
def test_provider(
    token: str = Form(...),
    config_id: int = Form(...),
) -> RedirectResponse:
    verify_admin_token(token)
    config = get_config(config_id, user_id=None)
    if config is None:
        return _redirect_with_test_result(token, ok=False, message="模型配置不存在。")

    result = test_provider_config(config)
    return _redirect_with_test_result(token, ok=result.ok, message=result.message)


def _is_valid_token(token: str | None) -> bool:
    try:
        verify_admin_token(token)
        return True
    except Exception:
        return False


def _render_form(token: str, config=None) -> str:
    config_id = "" if config is None else f'<input type="hidden" name="config_id" value="{config.id}">'
    provider_name = "" if config is None else escape(config.provider_name)
    base_url = "" if config is None else escape(config.base_url)
    model_name = "" if config is None else escape(config.model_name)
    checked = "checked" if config is None or config.enabled else ""
    api_key_required = "required" if config is None else ""
    api_key_placeholder = "新增时必填" if config is None else "留空则保留原密钥"

    return f"""
    <form method="post" action="/admin/providers/save" class="form">
      <input type="hidden" name="token" value="{escape(token)}">
      {config_id}
      <input type="hidden" name="provider_type" value="text">
      <p class="muted">模型类型：通用模型。图片识别和文字问答会优先使用前端当前选择的同一个模型。</p>
      <label>Provider 名称
        <input name="provider_name" value="{provider_name}" required>
      </label>
      <label>Base URL
        <input name="base_url" value="{base_url}" placeholder="https://example.com/v1" required>
      </label>
      <label>模型名称
        <input name="model_name" value="{model_name}" required>
      </label>
      <label>API Key / Token
        <input name="api_key" type="password" placeholder="{api_key_placeholder}" autocomplete="off" {api_key_required}>
      </label>
      <label class="check">
        <input name="enabled" type="checkbox" {checked}> 启用该配置
      </label>
      <button type="submit">保存配置</button>
    </form>
    """


def _render_config_card(config, token: str) -> str:
    return f"""
    <article class="card">
      <div class="card-head">
        <div>
          <strong>{escape(config.provider_name)}</strong>
          <span>通用模型 / {escape(config.model_name)}</span>
        </div>
        <em class="badge {'on' if config.enabled else ''}">{'启用' if config.enabled else '停用'}</em>
      </div>
      <p>{escape(config.base_url)}</p>
      <p class="muted">API Key：已加密保存，页面不回显明文。</p>
      <details>
        <summary>编辑</summary>
        {_render_form(token, config)}
      </details>
      <form method="post" action="/admin/providers/test" class="inline-form">
        <input type="hidden" name="token" value="{escape(token)}">
        <input type="hidden" name="config_id" value="{config.id}">
        <button type="submit" class="ghost">测试连接</button>
      </form>
      <form method="post" action="/admin/providers/delete" class="delete-form">
        <input type="hidden" name="token" value="{escape(token)}">
        <input type="hidden" name="config_id" value="{config.id}">
        <button type="submit" class="danger">删除</button>
      </form>
    </article>
    """


def _render_notice(status: str | None, message: str | None) -> str:
    if not status or not message:
        return ""
    class_name = "notice ok" if status == "ok" else "notice error"
    title = "测试成功" if status == "ok" else "测试失败"
    return f'<div class="{class_name}"><strong>{title}</strong><p>{escape(message)}</p></div>'


def _redirect_with_test_result(token: str, ok: bool, message: str) -> RedirectResponse:
    params = urlencode(
        {
            "token": token,
            "test_status": "ok" if ok else "error",
            "test_message": message,
        }
    )
    return RedirectResponse(url=f"/admin/providers?{params}", status_code=303)


def _page(title: str, body: str) -> str:
    return f"""
    <!doctype html>
    <html lang="zh-CN">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{escape(title)} - 薯安智检</title>
      <style>
        :root {{ color: #18201b; background: #f3f5ef; font-family: "Microsoft YaHei", sans-serif; }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; padding: 32px; }}
        .topbar, .layout {{ width: min(1180px, 100%); margin: 0 auto; }}
        .topbar {{ display: flex; justify-content: space-between; gap: 16px; align-items: end; margin-bottom: 18px; }}
        .layout {{ display: grid; grid-template-columns: 360px 1fr; gap: 16px; align-items: start; }}
        .panel, .card {{ border: 1px solid rgba(33,75,53,.16); border-radius: 8px; background: rgba(255,255,250,.94); }}
        .panel {{ padding: 22px; }}
        .narrow {{ width: min(460px, 100%); margin: 10vh auto 0; }}
        h1, h2, p {{ margin-top: 0; }}
        h1 {{ margin-bottom: 10px; font-size: 36px; }}
        h2 {{ font-size: 22px; }}
        p {{ color: #56665c; line-height: 1.7; }}
        .eyebrow {{ color: #6e7b44; font-size: 13px; font-weight: 700; }}
        .form {{ display: grid; gap: 12px; }}
        label {{ display: grid; gap: 6px; color: #405144; font-weight: 700; }}
        input, select {{ min-height: 40px; border: 1px solid rgba(33,75,53,.22); border-radius: 6px; padding: 8px 10px; font: inherit; }}
        .check {{ display: flex; align-items: center; gap: 8px; }}
        .check input {{ min-height: auto; }}
        button, .ghost {{ display: inline-flex; align-items: center; justify-content: center; border: 1px solid #214b35; border-radius: 6px; padding: 9px 13px; color: #fff; background: #214b35; text-decoration: none; font: inherit; cursor: pointer; }}
        .ghost {{ color: #214b35; background: transparent; }}
        .list {{ display: grid; gap: 12px; }}
        .card {{ padding: 16px; }}
        .card-head {{ display: flex; justify-content: space-between; gap: 12px; }}
        .card-head strong, .card-head span {{ display: block; }}
        .card-head span, .muted {{ margin-top: 4px; color: #56665c; }}
        .badge {{ padding: 4px 8px; border-radius: 999px; color: #7a493e; background: #f4e4dc; font-style: normal; font-weight: 700; }}
        .badge.on {{ color: #214b35; background: #dfeedd; }}
        details {{ margin-top: 12px; }}
        summary {{ cursor: pointer; color: #214b35; font-weight: 700; }}
        .inline-form, .delete-form {{ display: inline-flex; margin-top: 10px; margin-right: 8px; }}
        .danger {{ border-color: #a74435; color: #a74435; background: transparent; }}
        .empty {{ display: grid; place-items: center; min-height: 140px; border: 1px dashed rgba(33,75,53,.24); border-radius: 8px; }}
        .notice {{ margin-bottom: 14px; padding: 12px; border-radius: 8px; }}
        .notice p {{ margin: 6px 0 0; }}
        .notice.ok {{ color: #214b35; background: #dfeedd; }}
        .notice.error {{ color: #7a493e; background: #f4e4dc; }}
        code {{ color: #214b35; }}
        @media (max-width: 820px) {{
          body {{ padding: 18px; }}
          .topbar, .layout {{ grid-template-columns: 1fr; flex-direction: column; align-items: stretch; }}
        }}
      </style>
    </head>
    <body>{body}</body>
    </html>
    """
