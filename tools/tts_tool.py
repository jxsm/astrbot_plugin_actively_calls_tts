import os

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.api.message_components import Record
from astrbot.core.provider.provider import TTSProvider
from astrbot.core.agent.tool import FunctionTool, ToolExecResult
from astrbot.core.agent.run_context import ContextWrapper
from dataclasses import dataclass, field


@dataclass
class ActivelyCallTTSTool(FunctionTool):
    """让 LLM 主动调用 TTS 发送语音消息的工具"""

    name: str = "actively_send_voice_message"
    description: str = (
        "将文本转换为语音消息并发送给用户。"
        "当你想要用语音的方式回复用户时使用此工具，例如：情感表达、朗读内容、强调重点、增加互动趣味性等场景。"
        "注意：调用此工具后，你还需要用文字简要说明你发送了什么内容的语音。"
    )
    parameters: dict = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "要转换为语音的文本内容，建议控制在200字以内",
                },
            },
            "required": ["text"],
        }
    )

    # TTS 提供商，在插件初始化时注入
    _tts_provider: TTSProvider | None = field(default=None, repr=False)

    def set_tts_provider(self, provider: TTSProvider):
        """设置 TTS 提供商"""
        self._tts_provider = provider

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

        # 从上下文获取 event
        event: AstrMessageEvent | None = getattr(context.context, "event", None)
        if not event:
            return "错误：无法获取消息事件上下文"

        # 获取 TTS 提供商
        tts_provider = self._tts_provider
        if not tts_provider:
            return "错误：未配置 TTS 提供商，请在 AstrBot 设置中配置 TTS 服务"

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
