# astrbot_plugin_actively_calls_tts

AstrBot 主动调用 TTS 语音合成插件

## 功能特性

给 LLM 注册一个 TTS 工具，让 LLM 可以根据上下文**自主决定**何时发送语音消息。

与 AstrBot 原生的 TTS 回复概率设置不同，本插件让 LLM 具备了主动发送语音的能力，LLM 可以根据对话内容、情感表达需要等因素，智能地决定是否使用语音回复。

## 使用方法

1. 在 AstrBot 中配置 TTS 提供商（如 Edge TTS、OpenAI TTS 等）
2. 安装本插件
3. 与 LLM 对话时，LLM 会自动判断何时使用语音回复

## 工具说明

插件会向 LLM 注册一个名为 `actively_send_voice_message` 的工具：

- **名称**: `actively_send_voice_message`
- **描述**: 将文本转换为语音消息并发送给用户
- **参数**:
  - `text` (string, 必填): 要转换为语音的文本内容

## 适用场景

- 情感表达：用语音传达更丰富的情感
- 朗读内容：朗读诗歌、故事、文章等
- 强调重点：用语音强调重要信息
- 增加趣味：让对话更加生动有趣

## 注意事项

- 需要先在 AstrBot 中配置 TTS 提供商
- 建议语音文本控制在 200 字以内
- LLM 会根据上下文自动判断是否使用语音，不会每次都发语音
