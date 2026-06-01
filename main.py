from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger
from astrbot.api.provider import ProviderRequest

from .tools import ActivelyCallTTSTool


class ActivelyCallsTTS(Star):
    """主动调用 TTS 语音合成插件

    给 LLM 注册一个 TTS 工具，让 LLM 可以根据上下文自主决定何时发送语音消息。
    """

    def __init__(self, context: Context):
        super().__init__(context)

        # 创建 TTS 工具实例
        self.tts_tool = ActivelyCallTTSTool()

        # 获取 TTS 提供商并注入到工具中
        tts_provider = self.context.get_using_tts_provider()
        if tts_provider:
            self.tts_tool.set_tts_provider(tts_provider)
            logger.info("[ActivelyCallTTS] TTS 提供商已加载")
        else:
            logger.warning("[ActivelyCallTTS] 未检测到 TTS 提供商，请在 AstrBot 设置中配置")

        # 注册工具到 LLM
        self.context.add_llm_tools(self.tts_tool)
        logger.info("[ActivelyCallTTS] TTS 工具已注册到 LLM")

    @filter.on_llm_request()
    async def on_llm_request(self, event: AstrMessageEvent, req: ProviderRequest):
        """在每次 LLM 请求时，确保 TTS 提供商是最新的"""
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
