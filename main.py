import os
from dataclasses import dataclass, field

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.provider import ProviderRequest
from astrbot.api.star import Context, Star
from astrbot.api.message_components import Record
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.agent.run_context import ContextWrapper
from astrbot.core.provider.provider import TTSProvider


@dataclass
class ActivelyCallTTSTool(FunctionTool):
    """让 LLM 主动调用 TTS 发送语音消息的工具"""

    name: str = "actively_send_voice_message"
    description: str = "将文本转换为语音消息并发送给用户"
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要转换为语音的文本内容",
                },
            },
            "required": ["text"],
        }
    )

    # TTS 提供商，在插件初始化时注入
    _tts_provider: TTSProvider | None = field(default=None, repr=False)
    # 最大文本长度限制
    _max_text_length: int = field(default=200, repr=False)

    def set_tts_provider(self, provider: TTSProvider):
        """设置 TTS 提供商"""
        self._tts_provider = provider

    def set_max_text_length(self, length: int):
        """设置最大文本长度限制"""
        self._max_text_length = length

    async def call(self, context: ContextWrapper, **kwargs) -> ToolExecResult:
        """执行 TTS 转换并发送语音消息

        Args:
            context: 运行时上下文，包含 event 等信息
            **kwargs: 工具参数，包含 text

        Returns:
            ToolExecResult: 执行结果
        """
        text = kwargs.get("text", "")
        if not text or not text.strip():
            return "错误：文本内容不能为空"

        # 检查文本长度限制
        if self._max_text_length > 0 and len(text) > self._max_text_length:
            return f"错误：文本内容过长（{len(text)}字），请控制在{self._max_text_length}字以内"

        # 从上下文获取 event
        event: AstrMessageEvent | None = getattr(context.context, "event", None)
        if not event:
            return "错误：无法获取消息事件上下文"

        # 获取 TTS 提供商
        tts_provider = self._tts_provider
        if not tts_provider:
            return "错误：未配置 TTS 提供商，请在插件设置中选择 TTS 提供商"

        try:
            logger.info(f"[ActivelyCallTTS] LLM 主动调用 TTS: {text[:50]}...")

            # 调用 TTS 生成音频
            audio_path = await tts_provider.get_audio(text)

            if not audio_path or not os.path.exists(audio_path):
                return "错误：TTS 生成音频失败"

            # 发送语音消息
            record = Record(file=audio_path, url=audio_path)
            await event.send(event.chain_result([record]))

            logger.info("[ActivelyCallTTS] 语音消息发送成功")
            return f"语音消息发送成功，内容：{text}"

        except Exception as e:
            logger.error(f"[ActivelyCallTTS] 发送语音消息失败: {e}")
            return f"错误：发送语音消息失败 - {e!s}"


class ActivelyCallsTTS(Star):
    """主动调用 TTS 语音合成插件

    给 LLM 注册一个 TTS 工具，让 LLM 可以根据上下文自主决定何时发送语音消息。
    """

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config

        # 从配置中获取参数
        tool_name = config.get("tool_name", "actively_send_voice_message")
        tool_description = config.get(
            "tool_description",
            "将文本转换为语音消息并发送给用户。当你想要用语音的方式回复用户时使用此工具，例如：情感表达、朗读内容、强调重点、增加互动趣味性等场景。注意：调用此工具后，你还需要用文字简要说明你发送了什么内容的语音。"
        )
        text_param_desc = config.get(
            "text_param_description",
            "要转换为语音的文本内容，建议控制在200字以内"
        )
        max_text_length = config.get("max_text_length", 200)

        # 创建 TTS 工具实例
        self.tts_tool = ActivelyCallTTSTool()
        self.tts_tool.name = tool_name
        self.tts_tool.description = tool_description
        self.tts_tool.parameters = {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": text_param_desc,
                },
            },
            "required": ["text"],
        }
        self.tts_tool.set_max_text_length(max_text_length)

        # 获取 TTS 提供商
        tts_provider_id = config.get("tts_provider_id", "")
        if tts_provider_id:
            # 使用配置中指定的 TTS 提供商
            tts_provider = self._get_tts_provider_by_id(tts_provider_id)
        else:
            # 使用系统默认的 TTS 提供商
            tts_provider = self.context.get_using_tts_provider()

        if tts_provider:
            self.tts_tool.set_tts_provider(tts_provider)
            logger.info(f"[ActivelyCallTTS] TTS 提供商已加载: {tts_provider.meta().id}")
        else:
            logger.warning("[ActivelyCallTTS] 未检测到 TTS 提供商，请在插件设置中选择")

        # 注册工具到 LLM
        self.context.add_llm_tools(self.tts_tool)
        logger.info(f"[ActivelyCallTTS] TTS 工具已注册: {tool_name}")

    def _get_tts_provider_by_id(self, provider_id: str) -> TTSProvider | None:
        """根据 ID 获取 TTS 提供商"""
        for provider in self.context.get_all_tts_providers():
            if provider.meta().id == provider_id:
                return provider
        return None

    @filter.on_llm_request()
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """在每次 LLM 请求时，确保 TTS 提供商是最新的"""
        tts_provider_id = self.config.get("tts_provider_id", "")
        if tts_provider_id:
            tts_provider = self._get_tts_provider_by_id(tts_provider_id)
        else:
            tts_provider = self.context.get_using_tts_provider(umo=event.unified_msg_origin)

        if tts_provider and tts_provider != self.tts_tool._tts_provider:
            self.tts_tool.set_tts_provider(tts_provider)

    async def terminate(self):
        """插件卸载/停用时调用"""
        # 移除注册的工具
        try:
            tool_mgr = self.context.provider_manager.llm_tools
            tool_mgr.func_list = [
                t for t in tool_mgr.func_list if t.name != self.tts_tool.name
            ]
            logger.info("[ActivelyCallTTS] TTS 工具已移除")
        except Exception as e:
            logger.error(f"[ActivelyCallTTS] 移除工具失败: {e}")
