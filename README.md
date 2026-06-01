# astrbot_plugin_actively_calls_tts

AstrBot 主动调用 TTS 语音合成插件

## 功能特性

给 LLM 注册一个 TTS 工具，让 LLM 可以根据上下文**自主决定**何时发送语音消息。

与 AstrBot 原生的 TTS 回复概率设置不同，本插件让 LLM 具备了主动发送语音的能力，LLM 可以根据对话内容、情感表达需要等因素，智能地决定是否使用语音回复。

## 配置说明

### TTS 提供商

- **tts_provider_id**: 选择 TTS 提供商
  - 留空则使用系统默认的 TTS 提供商
  - 也可以手动选择已配置的 TTS 提供商（如 Edge TTS、OpenAI TTS 等）

### 工具配置

- **tool_name**: 工具名称（默认：`actively_send_voice_message`）
- **tool_description**: 工具描述，告诉 LLM 何时使用这个工具
- **text_param_description**: 文本参数描述
- **max_text_length**: 最大文本长度限制（默认：200字，0表示不限制）

## 使用方法

1. 在 AstrBot 中配置 TTS 提供商（Edge TTS、OpenAI TTS 等）
2. 安装本插件
3. 在插件设置中选择 TTS 提供商（可选）
4. 与 LLM 对话时，LLM 会自动判断何时使用语音回复

## 适用场景

- 情感表达：用语音传达更丰富的情感
- 朗读内容：朗读诗歌、故事、文章等
- 强调重点：用语音强调重要信息
- 增加趣味：让对话更加生动有趣

## 注意事项

- 建议在插件设置中明确选择 TTS 提供商，避免与系统默认 TTS 冲突
- 默认语音文本限制为 200 字，可在配置中调整
- LLM 会根据上下文自动判断是否使用语音，不会每次都发语音
