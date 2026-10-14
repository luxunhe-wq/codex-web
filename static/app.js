'use strict';
// Explicit UI translations only. Conversation text, filenames and project names stay untouched.
const EN_MESSAGES = {
  "语言": "Language",
  "部分思考耗时未提供": "Some reasoning durations are unavailable",
  "名称需为 1–80 个字符": "Name must contain 1–80 characters",
  "请先停止正在运行的任务": "Stop the running task first",
  "此请求已处理或已过期": "This request has been handled or has expired",
  "审批结果不正确": "Invalid approval decision",
  "回答格式不正确": "Invalid answer format",
  "移除文件 {name}": "Remove file {name}",
  "移除图片 {name}": "Remove image {name}",
  "Codex 首页": "Codex home",
  "Enter 发送": "Enter to send",
  "Shift + Enter 换行": "Shift + Enter for a new line",
  "一起找到问题的根源": "Find the cause together",
  "下载原文件": "Download original",
  "了解这个项目": "Explore this project",
  "从一个想法开始": "Start with an idea",
  "从这里，开始构建。": "Start building here.",
  "会话存储": "Conversation storage",
  "你的个人编程工作台": "Your personal coding workspace",
  "你的会话和项目保存在这台服务器上。": "Your conversations and projects are saved on this server.",
  "你的工作空间": "Your workspace",
  "例如 /home/user/projects": "e.g. /home/user/projects",
  "保存偏好": "Save preferences",
  "修改后，其他设备上的登录会立即失效。": "Changing these details immediately signs out other devices.",
  "停止任务": "Stop task",
  "关于": "About",
  "关闭侧栏": "Close sidebar",
  "关闭图片预览": "Close image preview",
  "关闭文件变更": "Close changes",
  "关闭文件夹选择": "Close folder picker",
  "关闭文件预览": "Close file preview",
  "关闭设置": "Close settings",
  "再次输入密码": "Enter your password again",
  "原图": "Original",
  "发送消息": "Send message",
  "取消": "Cancel",
  "变成下一步。": "into your next step.",
  "变更": "Changes",
  "只读": "Read only",
  "向 Codex 分配任务，或提出问题": "Give Codex a task or ask a question",
  "图片预览": "Image preview",
  "在浏览器里，继续你的编程工作。": "Continue coding in your browser.",
  "外观": "Appearance",
  "子文件夹": "Subfolders",
  "完全访问允许 Codex 操作项目以外的文件和命令。": "Full access allows Codex to run commands and access files outside the project.",
  "完全访问服务器": "Full server access",
  "实现一个新想法": "Build a new idea",
  "密码": "Password",
  "对话操作": "Conversation actions",
  "就绪": "Ready",
  "工作偏好": "Preferences",
  "工作空间": "Workspace",
  "当前密码": "Current password",
  "当前对话还没有文件变更。": "No file changes in this conversation yet.",
  "待发送附件": "Pending attachments",
  "思考强度": "Reasoning effort",
  "我想为当前项目添加一个新功能。请先了解项目，然后和我确认需求。": "I want to add a feature to this project. Explore it first, then confirm the requirements with me.",
  "我的账号": "My account",
  "打开": "Open",
  "打开侧栏": "Open sidebar",
  "执行审批": "Approvals",
  "执行权限": "Execution permissions",
  "把想法，": "Turn your ideas",
  "把需求变成可运行的功能": "Turn requirements into working features",
  "按需审批": "Ask when needed",
  "提出问题、修复问题，或把你的想法变成代码。": "Ask questions, fix problems, or turn your ideas into code.",
  "搜索对话": "Search conversations",
  "文件变更": "File changes",
  "文件夹路径": "Folder path",
  "文件预览": "File preview",
  "新密码": "New password",
  "新对话": "New conversation",
  "新对话使用此目录，已有对话保留原项目。": "New conversations use this folder. Existing conversations keep their project.",
  "新建对话": "New conversation",
  "无需审批": "Never ask",
  "显示密码": "Show password",
  "更新账号与密码": "Update account and password",
  "更深入": "Extra high",
  "更深入思考": "Extra high",
  "最大": "Maximum",
  "最大思考": "Maximum",
  "服务器上的绝对路径": "Absolute path on the server",
  "服务器本地保存": "Saved on this server",
  "本机 Codex App Server": "Local Codex App Server",
  "松开以添加文件或图片": "Drop to attach files or images",
  "极致": "Ultra",
  "极致思考": "Ultra",
  "查看本次文件变更": "View file changes",
  "标准": "Medium",
  "标准思考": "Medium",
  "梳理结构，找到开始的地方": "Understand the structure and where to start",
  "检查并修复问题": "Find and fix problems",
  "模型": "Model",
  "正在恢复你的对话…": "Restoring your conversation…",
  "正在连接": "Connecting",
  "浅色": "Light",
  "深入": "High",
  "深入思考": "High",
  "深色": "Dark",
  "添加一次，下次登录直接使用。": "Add once, use again next time.",
  "添加并使用": "Add and use",
  "添加并记住项目文件夹": "Add and remember a project folder",
  "添加文件夹": "Add folder",
  "添加文件或图片": "Attach files or images",
  "添加文件或图片，也可以粘贴或拖入": "Attach files or images, or paste and drop them",
  "添加项目文件夹": "Add project folder",
  "熟悉的 Codex 工作方式。": "The Codex workflow you know.",
  "版本": "Version",
  "独立社区项目，非 OpenAI 官方客户端。模型连接沿用你自己的 Codex 配置。": "An independent community project, not an official OpenAI client. Model access uses your own Codex configuration.",
  "现在，从浏览器开始。": "Now in your browser.",
  "理解项目 · 编写代码 · 验证结果": "Explore projects · Write code · Verify results",
  "留空使用服务器默认模型": "Leave blank for the server default",
  "登录": "Sign in",
  "登录你的工作台": "Sign in to your workspace",
  "确认密码": "Confirm password",
  "给 Codex 的消息": "Message to Codex",
  "继续你的对话，接着完成下一件事。": "Continue your conversations and take the next step.",
  "至少 10 位。若只修改账号，请填入当前密码。": "At least 10 characters. Enter your current password if only changing your username.",
  "让工作继续向前": "Keep work moving",
  "设置": "Settings",
  "请检查当前项目中的潜在问题，解释原因并提出修复建议。": "Check this project for potential problems, explain their causes, and suggest fixes.",
  "请阅读当前项目，介绍它的结构和运行方式。": "Explore this project and explain its structure and how to run it.",
  "谨慎审批": "Ask for untrusted actions",
  "账号": "Username",
  "账号与安全": "Account and security",
  "账号与密码": "Account and password",
  "账号与设置": "Account and settings",
  "跟随系统": "System",
  "轻量": "Low",
  "轻量思考": "Low",
  "输入密码": "Enter your password",
  "输入账号": "Enter your username",
  "返回上一级文件夹": "Go to parent folder",
  "连接你服务器上的 Codex": "Connected to Codex on your server",
  "连接方式": "Connection",
  "退出登录 ↗": "Sign out ↗",
  "选择 Codex 开始工作的目录和方式。": "Choose where and how Codex works.",
  "选择服务器上的项目目录，保存后可随时切换。": "Choose a project folder on the server and switch to it anytime.",
  "选择模型": "Choose model",
  "选文件前勾选，保留图片原始文件；传输会更慢": "Select before attaching to keep original images; uploads may take longer",
  "重新连接": "Reconnect",
  "项目": "Projects",
  "项目与会话列表": "Projects and conversations",
  "项目内读写": "Read and write in project",
  "项目内读写 · 按需审批": "Read and write in project · Ask when needed",
  "项目目录": "Project folder",
  "默认模型": "Default model",
  "已减少": "Reduced upload size by",
  "· 退出码": "· Exit code",
  "中新建对话": ": new conversation",
  "页": "page",
  "项目操作": "project actions",
  "% 上传流量，保留像素尺寸": "% while keeping image dimensions",
  "Codex 发生错误": "Codex encountered an error",
  "Codex 正在工作": "Codex is working",
  "Codex 连接中断，重新发送可恢复连接": "Codex disconnected. Send again to reconnect.",
  "上传": "Uploading",
  "上传失败": "Upload failed",
  "上传已取消": "Upload cancelled",
  "上传超时，请检查网络后重试": "Upload timed out. Check your connection and try again.",
  "不足 1 秒": "Less than 1 s",
  "两次输入的密码不一致": "Passwords do not match",
  "从列表移除": "Remove from list",
  "以下为文档页面预览。": "Document page previews are shown below.",
  "任务失败": "Task failed",
  "任务进行中": "Task in progress",
  "优化图片…": "Optimizing image…",
  "保留服务器文件和已有对话": "Keep server files and existing conversations",
  "其他对话": "Other conversations",
  "分钟": "min",
  "刚刚": "Just now",
  "创建你的工作台账号": "Create your workspace account",
  "创建账号并开始": "Create account",
  "图片": "Image",
  "图片附件": "Image attachment",
  "在": "In",
  "复制失败，请选择文字手动复制": "Copy failed. Select the text and copy it manually.",
  "密码至少 10 位，可在设置中随时修改。": "Use at least 10 characters. You can change it in settings.",
  "密码错误已达 6 次，请等待锁定结束。刷新页面不会解除锁定。": "Six failed password attempts. Wait for the lock to expire; refreshing will not unlock it.",
  "对话": "Conversation",
  "对话已归档": "Conversation archived",
  "对话暂未恢复：": "Conversation could not be restored: ",
  "小时": "h",
  "展开": "Expand",
  "工作偏好已保存": "Preferences saved",
  "已从列表移除，文件和对话已保留": "Removed from the list. Files and conversations were kept.",
  "已停止": "Stopped",
  "已复制": "Copied",
  "已完成": "Completed",
  "已思考": "Reasoned for",
  "已用时": "Elapsed",
  "已等待": "Waiting for",
  "已记录思考": "Recorded reasoning",
  "已请求停止任务": "Task stop requested",
  "已连接本机 Codex": "Connected to local Codex",
  "开始一段对话后，可以重命名或归档": "Start a conversation to rename or archive it.",
  "归档对话": "Archive conversation",
  "当前模型未提供思考摘要。": "This model did not provide a reasoning summary.",
  "思考": "Reasoning",
  "思考完成": "Reasoning complete",
  "思考摘要": "Reasoning summary",
  "思考耗时未提供": "Reasoning duration unavailable",
  "批准本次": "Approve once",
  "拒绝": "Decline",
  "提交回答": "Submit answers",
  "收起": "Collapse",
  "文件": "File",
  "文件夹较多，也可以直接输入目标路径。": "There are more folders. You can enter the destination path directly.",
  "查看图片": "View image",
  "预览": "Preview",
  "加载更早消息": "Load earlier messages",
  "复制": "Copy",
  "执行命令": "Run command",
  "展开查看思考摘要。": "Expand to view the reasoning summary.",
  "工作计划": "Plan",
  "调用工具": "Call tool",
  "搜索": "Search",
  "Codex 需要你的回答": "Codex needs your answer",
  "暂时无法连接服务器：": "Cannot connect to the server: ",
  "服务器返回了无效响应": "The server returned an invalid response",
  "服务器默认模型": "Server default model",
  "未提供思考摘要": "Reasoning summary unavailable",
  "查看操作内容，决定是否继续。": "Review the operation and decide whether to continue.",
  "校验图片…": "Validating image…",
  "插件与技能": "Plugins and skills",
  "插件功能正在更新，请等当前任务完成后刷新网页": "Plugin support is being updated. Refresh the website after the current task finishes.",
  "刷新列表": "Refresh list",
  "管理当前项目可用的插件和技能，设置保存在服务器上的 Codex 中。": "Manage plugins and skills available to this project. Settings are saved in Codex on the server.",
  "新增插件可先通过服务器终端的 codex plugin 命令安装；使用第三方服务的插件可能需要额外登录。": "Install new plugins with codex plugin in the server terminal. Plugins using third-party services may require additional sign-in.",
  "正在加载插件与技能…": "Loading plugins and skills…",
  "当前项目：{name}": "Current project: {name}",
  "已安装插件": "Installed plugins",
  "可用技能": "Available skills",
  "尚未安装插件，可先在服务器上安装，再刷新列表。": "No installed plugins. Install them on the server, then refresh this list.",
  "当前项目没有发现技能。": "No skills found for this project.",
  "启用": "Enable",
  "禁用": "Disable",
  "已启用": "Enabled",
  "已禁用": "Disabled",
  "暂不可用": "Unavailable",
  "在对话中使用": "Use in conversation",
  "设置已保存，建议在新对话中使用": "Settings saved. Start a new conversation to use them.",
  "请使用这个技能完成以下任务：": "Use this skill for the following task: ",
  "部分插件或技能未能加载，请检查服务器配置后刷新。": "Some plugins or skills could not load. Check the server configuration and refresh.",
  "当前 Codex 版本不支持此插件或技能接口，请升级 Codex": "This Codex version does not support this plugin or skill API. Upgrade Codex.",
  "插件列表暂时无法读取，请稍后刷新重试": "The plugin list could not be loaded. Refresh and try again.",
  "技能列表暂时无法读取，请稍后刷新重试": "The skill list could not be loaded. Refresh and try again.",
  "插件设置暂时无法读取，请稍后刷新重试": "Plugin settings could not be updated. Refresh and try again.",
  "技能设置暂时无法读取，请稍后刷新重试": "Skill settings could not be updated. Refresh and try again.",
  "插件尚未安装或已被移除，请刷新列表": "This plugin is not installed or has been removed. Refresh the list.",
  "技能不存在或已被移除，请刷新列表": "This skill is missing or has been removed. Refresh the list.",
  "此插件当前不可用，请检查 Codex 账号或管理员配置": "This plugin is unavailable. Check your Codex account or administrator configuration.",
  "请等所有任务完成后再修改插件或技能": "Wait for all tasks to finish before changing plugins or skills.",
  "插件设置不正确": "Invalid plugin settings",
  "技能设置不正确": "Invalid skill settings",
  "技能选择不正确": "Invalid skill selection",
  "所选技能已禁用或不属于当前项目，请重新选择": "The selected skill is disabled or unavailable in this project. Select it again.",
  "等待确认 {seconds} 秒": "Awaiting confirmation {seconds}s",
  "图片仍在传输或等待服务器确认，尚未完成上传。": "The image is still in transit or awaiting server confirmation. Upload is not complete yet.",
  "文件仍在传输或等待服务器处理，尚未完成上传。": "The file is still in transit or awaiting server processing. Upload is not complete yet.",
  "模型列表暂不可用：": "Model list unavailable: ",
  "模型已更新，将在下次发送时使用": "Model updated. It will be used for your next message.",
  "模型未提供可单独计量的思考耗时。任务总用时和等待回复时间会继续显示。": "The model did not provide a separate reasoning duration. Total task time and waiting time are still shown.",
  "正在分析任务": "Analyzing the task",
  "正在加载对话…": "Loading conversation…",
  "正在加载文件变更…": "Loading file changes…",
  "正在加载更早消息…": "Loading earlier messages…",
  "正在发送任务": "Sending task",
  "正在思考": "Reasoning",
  "正在思考 / 等待回复": "Reasoning / waiting for a response",
  "正在执行命令": "Running command",
  "正在读取文件…": "Reading file…",
  "正在读取文件夹…": "Reading folders…",
  "此工具请求暂不支持": "This tool request is not supported yet",
  "此文件夹中没有子文件夹，可以直接添加。": "This folder has no subfolders. You can add it directly.",
  "此文件暂无文本预览，可下载原文件或让 Codex 分析。": "No text preview is available. Download the original or ask Codex to analyze it.",
  "每个文件最大 25 MB": "Each file can be up to 25 MB",
  "每张图片最大 10 MB": "Each image can be up to 10 MB",
  "每条消息最多添加 8 个附件": "Up to 8 attachments per message",
  "没有找到匹配的对话。": "No matching conversations.",
  "消息已发送，历史暂未加载：": "Message sent; history could not be loaded: ",
  "添加一个项目文件夹，\n从这里开始工作。": "Add a project folder\nand start working here.",
  "登录已失效，请重新登录": "Your session expired. Please sign in again.",
  "移除": "Remove",
  "移除图片": "Remove image",
  "第": "Page",
  "等待上传…": "Waiting to upload…",
  "等待你的确认": "Awaiting your confirmation",
  "等待输出…": "Waiting for output…",
  "粘贴的图片.png": "pasted-image.png",
  "网络连接中断，请重试上传": "Connection interrupted. Try uploading again.",
  "耗时未提供": "Duration unavailable",
  "自定义回答": "Custom answer",
  "解析文件…": "Parsing file…",
  "请回答所有问题": "Please answer all questions",
  "请求失败": "Request failed",
  "账号与密码已更新，其他登录已失效": "Account and password updated. Other sessions were signed out.",
  "跳过请求": "Skip request",
  "输入你的回答": "Enter your answer",
  "输入对话名称": "Enter a conversation name",
  "运行中": "Running",
  "连接中，自动重试": "Connecting; retrying automatically",
  "连续输错 6 次锁定 6 分钟，成功登录后清零。": "Six failed attempts lock sign-in for 6 minutes. Successful sign-in resets the counter.",
  "选择一个回答": "Choose an answer",
  "选择项目": "Select project",
  "部分": "Partial",
  "重命名对话": "Rename conversation",
  "重新上传图片": "Upload image again",
  "重试": "Retry",
  "附件上传失败": "Attachment upload failed",
  "隐藏密码": "Hide password",
  "需要你的批准": "Approval required",
  "项目文件夹已保存，下次登录可直接使用": "Project folder saved for your next sign-in.",
  "预览展示部分内容，原文件可完整下载。": "The preview shows part of the content. Download the full original file.",
  "预览文件": "Preview file",
  "首次使用，设置一个只有你知道的账号和密码。": "Create a private username and password to get started.",
  "支持 PNG、JPEG、WebP 和 GIF 图片": "PNG, JPEG, WebP and GIF images are supported",
  "图片无法读取，请重新选择": "Cannot read the image. Please select it again.",
  "图片尺寸过大，请缩小后重试": "Image dimensions are too large. Resize it and try again.",
  "图片数据损坏或不完整，请重新选择原图": "Image data is damaged or incomplete. Please select the original image again.",
  "请输入文件夹的绝对路径，例如 /home/user/projects": "Enter an absolute folder path, e.g. /home/user/projects",
  "此路径不是文件夹": "This path is not a folder",
  "文件夹不存在，请检查路径": "Folder not found. Check the path.",
  "没有权限访问此文件夹": "Permission denied for this folder",
  "无法访问此文件夹，请检查路径": "Cannot access this folder. Check the path.",
  "账号需为 3–40 位字母、数字、中文或 . @ _ -": "Use 3–40 letters, digits, Chinese characters or . @ _ - for the username",
  "密码长度需为 10–256 位": "Password must contain 10–256 characters",
  "文件路径不正确": "Invalid file path",
  "只能查看当前项目中的文件": "Only files in the current project can be viewed",
  "敏感文件不可预览": "Sensitive files cannot be previewed",
  "仅支持普通文本文件": "Only regular text files are supported",
  "硬链接文件不可预览": "Hard-linked files cannot be previewed",
  "文件过大，请在本机查看": "File too large. View it locally.",
  "仅支持文本文件预览": "Only text file previews are supported",
  "文件不存在": "File not found",
  "文件不可预览（不支持符号链接）": "Cannot preview the file (symbolic links are not supported)",
  "图片附件不正确": "Invalid image attachment",
  "图片附件不存在，请重新添加": "Image attachment not found. Attach it again.",
  "图片附件无法读取，请重新添加": "Cannot read the image attachment. Attach it again.",
  "页面不存在": "Page not found",
  "页面无法读取": "Cannot read the page",
  "图片类型与文件内容不一致": "Image type does not match its contents",
  "文件解析超时，请拆分或简化后上传": "File parsing timed out. Split or simplify the file and upload it again.",
  "文件内容过大或过于复杂，请拆分后上传": "File contents are too large or complex. Split the file and upload it again.",
  "登录已锁定，请在倒计时结束后重试": "Sign-in is locked. Try again when the countdown ends.",
  "密码修改已锁定，请在倒计时结束后重试": "Password changes are locked. Try again when the countdown ends.",
  "密码错误已达 6 次，登录锁定 6 分钟": "Six failed password attempts. Sign-in is locked for 6 minutes.",
  "密码错误已达 6 次，密码修改锁定 6 分钟": "Six failed password attempts. Password changes are locked for 6 minutes.",
  "会话不存在": "Conversation not found",
  "无法启动 Codex，请确认服务器已安装 Codex": "Cannot start Codex. Make sure it is installed on the server.",
  "Codex 连接已断开，请重新发送": "Codex disconnected. Send again to reconnect.",
  "Codex 响应超时，请稍后重试": "Codex response timed out. Try again later.",
  "Codex 请求失败": "Codex request failed",
  "Codex 服务已断开": "Codex service disconnected",
  "尝试次数过多，请在 15 分钟后重试": "Too many attempts. Try again in 15 minutes.",
  "请求主机不正确": "Invalid request host",
  "拒绝跨站请求": "Cross-site request rejected",
  "请求来源不正确": "Invalid request origin",
  "请先登录": "Please sign in first",
  "请求验证失败，请刷新页面": "Request verification failed. Refresh the page.",
  "请求格式不正确": "Invalid request format",
  "请求内容过大": "Request too large",
  "服务暂时不可用": "Service temporarily unavailable",
  "没有权限浏览此文件夹": "Permission denied when browsing this folder",
  "无法读取此文件夹": "Cannot read this folder",
  "历史消息分页参数不正确": "Invalid history pagination parameters",
  "接口不存在": "API endpoint not found",
  "事件游标不正确": "Invalid event cursor",
  "请求失败，请稍后重试": "Request failed. Try again later.",
  "附件类型不正确": "Invalid attachment type",
  "图片上传请求不正确": "Invalid image upload request",
  "图片上传不完整，请重试": "Image upload incomplete. Try again.",
  "账号已创建，请登录": "An account already exists. Please sign in.",
  "远程部署请在服务器运行 python server.py --init-admin 创建管理员": "For remote deployment, run python server.py --init-admin on the server to create an administrator",
  "已发送的图片保留在对话历史中": "Sent images are kept in conversation history",
  "当前密码错误": "Incorrect current password",
  "项目文件夹不在列表中": "Project folder is not in the list",
  "执行权限设置不正确": "Invalid execution permission setting",
  "主题设置不正确": "Invalid theme setting",
  "思考强度不正确": "Invalid reasoning effort",
  "模型设置不正确": "Invalid model setting",
  "项目目录必须是服务器上已存在的绝对路径": "Project folder must be an existing absolute path on the server",
  "每条消息最多添加 8 个附件，请检查附件": "Up to 8 attachments per message. Check your attachments.",
  "请输入消息或添加附件，文字最多 100000 个字符": "Enter a message or attach files. Text is limited to 100000 characters.",
  "会话已归档": "Conversation archived",
  "请等待当前任务结束，或先停止任务": "Wait for the current task to finish, or stop it first.",
  "此附件属于其他对话，请重新添加": "This attachment belongs to another conversation. Attach it again.",
  "PDF 已加密，请先解密后上传": "The PDF is encrypted. Decrypt it before uploading.",
  "PDF 无法读取，请检查文件是否损坏": "Cannot read the PDF. Check whether it is damaged.",
  "文件解压后的内容过大，请拆分后上传": "Uncompressed file contents are too large. Split the file and upload it again.",
  "文件内部内容过大，请拆分后上传": "Internal file contents are too large. Split the file and upload it again.",
  "文档 XML 格式不受支持": "Document XML format is not supported",
  "PowerPoint 文档没有可读取的幻灯片": "The PowerPoint document has no readable slides",
  "Excel 工作表无法读取": "Cannot read the Excel worksheet",
  "文档无法读取，请检查格式或文件是否损坏": "Cannot read the document. Check the format and whether it is damaged.",
  "此格式未自动提取文本，Codex 可以按需读取原文件。": "Text was not extracted automatically for this format. Codex can read the original file as needed.",
  "文件较长，当前展示部分内容，原文件已保留供继续读取。": "This file is long. Part of the content is shown; the original is kept for further reading.",
  "文件内容无法读取": "Cannot read the file contents",
  "文件附件": "File attachment",
  "秒": "s",
  "分": "min",
  "· 耗时": "· Elapsed",
  "登录已锁定 ·": "Sign-in locked ·",
  "{count} 分钟": "{count} min ago",
  "{count} 小时": "{count} h ago",
  "{seconds} 秒": "{seconds} s",
  "{minutes} 分 {seconds} 秒": "{minutes} min {seconds} s",
  "在 {name} 中新建对话": "New conversation in {name}",
  "第 {number} 页": "Page {number}",
  "创建账号并开始 <span>→</span>": "Create account <span>→</span>",
  "登录 <span>→</span>": "Sign in <span>→</span>",
  "<button type=\"button\" id=\"load-history\">加载更早消息</button><span id=\"history-status\" class=\"muted\"></span>": "<button id=\"load-history\" type=\"button\">Load earlier messages</button><span class=\"muted\" id=\"history-status\"></span>",
  "<span class=\"missing-image\">图片附件</span>": "<span class=\"missing-image\">Image attachment</span>",
  "<span class=\"missing-image\">文件附件</span>": "<span class=\"missing-image\">File attachment</span>",
  "<p class=\"muted\">当前模型未提供思考摘要。</p>": "<p class=\"muted\">This model did not provide a reasoning summary.</p>",
  "<p class=\"muted\">当前对话还没有文件变更。</p>": "<p class=\"muted\">No file changes in this conversation yet.</p>",
  "<h3>Codex 需要你的回答</h3>": "<h3>Codex needs your answer</h3>"
};
const LANGUAGE_STORAGE_KEY = 'codex-web-language';
let uiLanguage = 'zh-CN';
try { if (localStorage.getItem(LANGUAGE_STORAGE_KEY) === 'en') uiLanguage = 'en'; } catch { /* Storage is optional. */ }
document.documentElement.lang = uiLanguage;
const staticTranslations = [];
const originalUIStrings = new Map(Object.entries(EN_MESSAGES).map(([source, translated]) => [translated, source]));
function t(message, values = {}) {
  const text = String(message ?? '');
  const key = text.trim();
  const translated = uiLanguage === 'en' ? (EN_MESSAGES[key] ?? key) : key;
  return (text.slice(0, text.length - text.trimStart().length) + translated + text.slice(text.trimEnd().length))
    .replace(/\{(\w+)\}/g, (match, name) => Object.hasOwn(values, name) ? String(values[name]) : match);
}
function sourceUIMessage(message) {
  const text = String(message || '');
  const attempts = text.match(/^(Incorrect username or password|Incorrect current password)\. (\d+) attempts remaining\.$/);
  if (attempts) return (attempts[1] === 'Incorrect current password' ? '当前密码错误' : '账号或密码错误') + `，还可尝试 ${attempts[2]} 次`;
  return originalUIStrings.get(text) || text;
}
function translateError(message) {
  const source = sourceUIMessage(message);
  if (uiLanguage === 'en') {
    const attempts = source.match(/^(账号或密码错误|当前密码错误)，还可尝试 (\d+) 次$/);
    if (attempts) return (attempts[1] === '当前密码错误' ? 'Incorrect current password' : 'Incorrect username or password') + `. ${attempts[2]} attempts remaining.`;
  }
  return t(source);
}
function captureStaticTranslations() {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    if (node.parentElement?.closest('script, style, [data-language-picker], [data-startup-lang], #chat-title, #account-name, #project-name, #composer-project, #image-dialog-title, #text-dialog-title, #file-dialog-title, #folder-current-path')) continue;
    if (Object.hasOwn(EN_MESSAGES, node.nodeValue.trim())) staticTranslations.push({node, source: node.nodeValue, last: node.nodeValue});
  }
  for (const node of document.querySelectorAll('[title], [placeholder], [aria-label], [alt], [data-prompt]')) {
    for (const attribute of ['title', 'placeholder', 'aria-label', 'alt', 'data-prompt']) {
      const source = node.getAttribute(attribute);
      if (source && Object.hasOwn(EN_MESSAGES, source.trim())) staticTranslations.push({node, attribute, source, last: source});
    }
  }
}
function applyStaticLanguage() {
  document.documentElement.lang = uiLanguage;
  for (const entry of staticTranslations) {
    if (!entry.node.isConnected) continue;
    const current = entry.attribute ? entry.node.getAttribute(entry.attribute) : entry.node.nodeValue;
    // Dynamic UI/user values take ownership of a node when they replace its initial label.
    if (current !== entry.last) continue;
    const value = t(entry.source);
    if (entry.attribute) entry.node.setAttribute(entry.attribute, value);
    else entry.node.nodeValue = value;
    entry.last = value;
  }
  for (const picker of document.querySelectorAll('[data-language-picker]')) { picker.value = uiLanguage; for (const option of picker.options) option.defaultSelected = option.value === uiLanguage; }
}
function setUILanguage(language, {remember = true} = {}) {
  if (!['zh-CN', 'en'].includes(language) || language === uiLanguage) return;
  const notices = ['toast', 'auth-error', 'project-error', 'general-error', 'credentials-error'].map(id => {
    const node = document.getElementById(id);
    return [node, sourceUIMessage(node.textContent)];
  });
  uiLanguage = language;
  if (remember) try { localStorage.setItem(LANGUAGE_STORAGE_KEY, language); } catch { /* Keep switching usable without storage. */ }
  applyStaticLanguage();
  if (!$('auth-screen').hidden) {
    renderAuthCopy(); updateLoginLock();
    $('password-toggle').setAttribute('aria-label', t($('auth-password').type === 'password' ? '显示密码' : '隐藏密码'));
  }
  if (!$('startup-screen').hidden && $('startup-retry').hidden) $('startup-message').textContent = t('正在恢复你的对话…');
  if (!$('workspace').hidden) {
    const scrollTop = $('scroll-area').scrollTop;
    const pinned = pinToBottom;
    const expanded = new Set([...$('messages').querySelectorAll('details[open]')].map(node => node.dataset.itemId));
    const requestDrafts = [...$('requests').querySelectorAll('input, select')].map(node => ({value: node.value, hidden: node.hidden}));
    const errors = [...$('messages').querySelectorAll('.error-message')].map(node => sourceUIMessage(node.textContent));
    document.querySelector('.project-menu-popover')?.remove(); document.querySelector('.thread-menu-popover')?.remove();
    applySettings(); renderThreadList();
    if (!state.thread) $('chat-title').textContent = t('新对话');
    if ($('model-picker').options[0]?.value === '') $('model-picker').options[0].text = t('服务器默认模型');
    if ($('history-control')) $('load-history').textContent = t('加载更早消息');
    resetMessageCache(); pinToBottom = false; renderMessages(); renderRequests(); renderAttachments(); historyControl();
    for (const node of $('messages').querySelectorAll('details')) if (expanded.has(node.dataset.itemId)) { node.open = true; const item = state.items.find(item => item.id === node.dataset.itemId); if (item) renderToolBody(node, item); }
    [...$('requests').querySelectorAll('input, select')].forEach((node, index) => { if (requestDrafts[index]) { node.value = requestDrafts[index].value; node.hidden = requestDrafts[index].hidden; } });
    for (const error of errors) appendError(error);
    $('scroll-area').scrollTop = scrollTop; pinToBottom = pinned;
    setConnection(!!state.connected);
    renderExtensions();
  }
  for (const [node, source] of notices) if (source) node.textContent = translateError(source);
}
window.addEventListener('storage', event => {
  if (event.key !== LANGUAGE_STORAGE_KEY) return;
  const update = () => setUILanguage(event.newValue === 'en' ? 'en' : 'zh-CN', {remember: false});
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', update, {once: true});
  else update();
});

const $ = id => document.getElementById(id);
const state = { csrf: '', username: '', settings: {}, projects: [], threads: [], thread: null, items: [], turns: [], attachments: [], requests: [], seq: 0, threadSeq: 0, stream: null, setup: false, sending: false, models: [], selection: 0, serverOffset: 0 };
let toastTimer, renderFrame, threadRefreshTimer;
const messageNodes = new Map();
const messageVersions = new Map();
const dirtyItems = new Set();
let renderedThread, changesVersion = '', changesDirty = true, pinToBottom = true, threadListRequest = 0;
function setText(node, text) { if (node.textContent !== text) node.textContent = text; }
let authLockedUntil = 0, authPending = false, lockWasActive = false;
let folderBrowseRequest = 0, folderParent = null, projectSwitchRequest = 0;
const MAX_IMAGES = 8, MAX_IMAGE_BYTES = 10 * 1024 * 1024;
const MAX_FILE_BYTES = 25 * 1024 * 1024;
let imageSequence = 0, imageDragDepth = 0;
const uploadQueue = [];
let activeUploads = 0;
const HISTORY_PAGE_SIZE = 80, threadCache = new Map();
let navigationController, projectSaveChain = Promise.resolve(), changesRequest = 0, pendingProjectPath = null;
let collapsedProjects = new Set();
try { collapsedProjects = new Set(JSON.parse(localStorage.getItem('codex-web-collapsed-projects') || '[]')); } catch { /* Start expanded if browser storage is unavailable. */ }
const escapeHTML = text => String(text ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function toast(message) { $('toast').textContent = t(message); $('toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true, 3800); }
function savedThread() {
  for (const name of ['sessionStorage', 'localStorage']) {
    try { const id = window[name].getItem('codex-web-thread'); if (id) return id; } catch { /* Storage may be unavailable. */ }
  }
  return null;
}
function rememberThread(id) {
  for (const name of ['sessionStorage', 'localStorage']) {
    try { if (id) window[name].setItem('codex-web-thread', id); else window[name].removeItem('codex-web-thread'); } catch { /* Authentication lives in the HttpOnly cookie. */ }
  }
}
async function api(path, body, options = {}) {
  const response = await fetch('/api' + path, {method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin', headers: body === undefined ? {} : {'Content-Type':'application/json', 'X-CSRF-Token': state.csrf}, body: body === undefined ? undefined : JSON.stringify(body), ...options});
  let data;
  try { data = await response.json(); } catch { throw new Error(t('服务器返回了无效响应')); }
  if (!response.ok) { if (response.status === 401 && !['/login','/setup'].includes(path)) showAuth(false); const error = new Error(translateError(data.error || '请求失败')); error.status = response.status; error.details = data; throw error; }
  return data;
}
function showAuth(setup) {
  $('startup-screen').hidden = true;
  navigationController?.abort(); threadCache.clear();
  clearAttachments();
  state.setup = setup;
  if (state.stream) state.stream.close();
  state.stream = null; state.csrf = '';
  state.thread = null; state.items = []; state.turns = []; state.requests = []; state.threads = []; state.projects = []; state.selection++; state.loadingThread = null;
  state.hasMore = false; state.before = null; state.allChanges = null; state.changePaths = [];
  if ($('history-control')) $('history-control').hidden = true;
  for (const dialog of document.querySelectorAll('dialog[open]')) dialog.close();
  $('workspace').hidden = true; $('auth-screen').hidden = false;
  renderAuthCopy();
  $('auth-form').reset(); $('auth-error').textContent = '';
  $('auth-submit').disabled = !setup;
  $('auth-username').focus();
  if (!setup) refreshLoginLock();
}
function renderAuthCopy() {
  const setup = state.setup;
  $('auth-title').textContent = setup ? t('创建你的工作台账号') : t('登录你的工作台');
  $('auth-eyebrow').textContent = setup ? 'A FRESH START' : 'WELCOME BACK';
  $('auth-desc').textContent = setup ? t('首次使用，设置一个只有你知道的账号和密码。') : t('继续你的对话，接着完成下一件事。');
  $('auth-submit').innerHTML = setup ? t('创建账号并开始 <span>→</span>') : t('登录 <span>→</span>');
  $('confirm-label').hidden = !setup; $('auth-confirm').required = setup;
  $('auth-password').autocomplete = setup ? 'new-password' : 'current-password';
  $('auth-password').minLength = setup ? 10 : 1;
  $('auth-note').textContent = setup ? t('密码至少 10 位，可在设置中随时修改。') : t('连续输错 6 次锁定 6 分钟，成功登录后清零。');
}
function setLoginLock(details) {
  authLockedUntil = details.retryAfter > 0 ? Date.now() + details.retryAfter * 1000 : 0;
  updateLoginLock();
}
function updateLoginLock() {
  if ($('auth-screen').hidden || state.setup) return;
  const seconds = Math.max(0, Math.ceil((authLockedUntil - Date.now()) / 1000));
  const locked = seconds > 0;
  $('auth-submit').disabled = locked || authPending;
  $('auth-username').disabled = locked; $('auth-password').disabled = locked;
  $('auth-submit').innerHTML = locked ? `${escapeHTML(t("登录已锁定 · "))}${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2,'0')}` : t('登录 <span>→</span>');
  if (locked) $('auth-error').textContent = t('密码错误已达 6 次，请等待锁定结束。刷新页面不会解除锁定。');
  else if (lockWasActive) { $('auth-error').textContent = ''; $('auth-password').value = ''; refreshLoginLock(); }
  lockWasActive = locked;
}
async function refreshLoginLock() {
  if (authPending || state.setup || $('auth-screen').hidden) return;
  try { const status = await api('/status'); if (!$('auth-screen').hidden && !state.setup) setLoginLock(status); } catch { /* Keep the last server-confirmed lock if temporarily disconnected. */ }
}

async function enterWorkspace(data) {
  $('startup-screen').hidden = true;
  state.csrf = data.csrf; state.username = data.username; state.settings = data.settings; state.projects = data.projects || []; state.seq = data.seq || 0;
  $('auth-screen').hidden = true; $('workspace').hidden = false;
  $('account-name').textContent = state.username; $('avatar').textContent = state.username.slice(0,1).toUpperCase();
  state.threads = data.threads || [];
  applySettings(); renderMessages(); renderThreadList();
  connectEvents();
  loadModels();
  if (!data.threads) await refreshThreads();
  const saved = savedThread();
  if (data.conversation) { state.selection++; displayThread(data.conversation); }
  else if (saved && state.threads.some(t => t.id === saved)) await selectThread(saved);
}
function applyTheme() {
  const theme = state.settings.theme;
  document.documentElement.dataset.theme = theme === 'system' ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : (theme || 'light');
}
function applySettings() {
  applyTheme();
  if (!state.thread) $('chat-title').textContent = t('新对话');
  const s = state.settings;
  const cwd = state.thread?.cwd || s.cwd || '';
  const name = cwd.split('/').filter(Boolean).at(-1) || '/';
  $('project-name').textContent = name; $('composer-project').textContent = name; $('project-button').title = cwd;
  $('effort-picker').value = s.effort || 'high';
  const model = s.model || '';
  if (model && ![...$('model-picker').options].some(o => o.value === model)) $('model-picker').add(new Option(model,model));
  $('model-picker').value = model;
  $('permission-label').textContent = ({'read-only':t('只读'),'workspace-write':t('项目内读写'),'danger-full-access':t('完全访问服务器')}[s.sandbox] || t('项目内读写')) + ' · ' + ({'on-request':t('按需审批'),'untrusted':t('谨慎审批'),'never':t('无需审批')}[s.approvalPolicy] || t('按需审批'));
}
async function loadModels() {
  try {
    const {data} = await api('/models'); state.models = data;
    const picker = $('model-picker'); picker.replaceChildren(new Option(t('服务器默认模型'),''));
    $('model-options').replaceChildren();
    for (const m of data) { picker.add(new Option(m.displayName || m.model, m.model)); const option = document.createElement('option'); option.value = m.model; $('model-options').append(option); }
    applySettings(); setConnection(true);
  } catch (e) { setConnection(false); toast(t('模型列表暂不可用：') + e.message); }
}
function setConnection(connected) { state.connected = connected; $('connection-dot').classList.toggle('offline',!connected); $('connection-label').textContent = connected ? t('已连接本机 Codex') : t('连接中，自动重试'); }
function connectEvents() {
  if (state.stream) state.stream.close();
  const source = new EventSource('/api/events?after=' + state.seq); state.stream = source;
  source.onopen = () => { if (state.stream === source) setConnection(true); };
  source.onerror = () => { if (state.stream === source) setConnection(false); };
  source.addEventListener('expired', () => { source.close(); if (state.stream !== source) return; showAuth(false); toast(t('登录已失效，请重新登录')); });
  source.onmessage = event => {
    state.seq = Math.max(state.seq, Number(event.lastEventId) || 0);
    const obj = JSON.parse(event.data), method = obj.method, p = obj.params || {};
    if (p.webTimestamp) state.serverOffset = p.webTimestamp * 1000 - Date.now();
    if (method === 'web/projectsChanged') {
      state.projects = p.projects || []; state.settings.cwd = pendingProjectPath || p.cwd;
      applySettings(); renderThreadList(); return;
    }
    if (method === 'web/resync' || method === 'web/disconnected') {
      for (const cached of threadCache.values()) { cached.stale = true; cached.pendingEvents = []; }
      if (method === 'web/disconnected') { setConnection(false); toast(t('Codex 连接中断，重新发送可恢复连接')); }
      refreshThreads().catch(e => toast(e.message));
      refreshProjects().catch(e => toast(e.message));
      if (state.thread) selectThread(state.thread.id, {force: true}).catch(e => toast(e.message));
      return;
    }
    const tid = method === 'web/request' ? p.params?.threadId : p.threadId;
    if (!tid) return;
    const eventId = Number(event.lastEventId);
    const cached = threadCache.get(tid);
    if (cached && state.thread?.id !== tid && !cached.stale) {
      cached.pendingEvents ||= [];
      if (cached.pendingEvents.length < 500) cached.pendingEvents.push({method, p, eventId, tid});
      else { cached.pendingEvents = []; cached.stale = true; }
    }
    if (['turn/started','turn/completed','web/request','web/responded'].includes(method)) scheduleThreadRefresh();
    if (state.loadingThread?.id === tid) {
      state.loadingThread.events.push({method, p, eventId, tid, serverOffset: state.serverOffset});
      return;
    }
    applyThreadEvent(method, p, eventId, tid);
  };
}
function applyThreadEvent(method, p, eventId, tid) {
  if (!state.thread || tid !== state.thread.id || eventId <= state.threadSeq) return;
  state.threadSeq = eventId;
  if (p.webTurn) {
    const index = state.turns.findIndex(t => t.id === p.webTurn.id);
    if (index >= 0) state.turns[index] = p.webTurn; else state.turns.push(p.webTurn);
  }
  if (method === 'turn/started') { state.thread.status = 'running'; state.thread.turn_id = p.turn.id; }
  if (method === 'turn/completed') { state.thread.status = p.turn.status || 'completed'; state.thread.turn_id = null; state.requests = []; if (p.turn.error) appendError(p.turn.error.message || t('任务失败')); }
  if (method === 'item/started' || method === 'item/completed') {
    if (p.item.type === 'userMessage') state.items = state.items.filter(item => !item.webPending);
    const index = state.items.findIndex(item => item.id === p.item.id);
    if (index >= 0) state.items[index] = p.item; else state.items.push(p.item);
    dirtyItems.add(p.item.id);
    if (p.item.type === 'fileChange') changesDirty = true;
    if (p.item.type === 'fileChange') state.allChanges = null;
  }
  if (method.endsWith('/delta') || method.endsWith('Delta')) {
    const item = state.items.find(item => item.id === p.itemId);
    if (item) {
      if (method.includes('reasoning')) {
        if (p.delta && item.webTiming) item.webTiming.streamed = true;
        if (method.includes('summaryTextDelta')) {
          const index = Math.max(0, Number(p.summaryIndex) || 0); item.summary ||= [];
          while (item.summary.length <= index) item.summary.push('');
          item.summary[index] += p.delta || '';
        }
      } else {
        const field = method.includes('commandExecution') ? 'aggregatedOutput' : 'text';
        item[field] = (item[field] || '') + (p.delta || '');
      }
      dirtyItems.add(item.id);
      if (item.type === 'fileChange') changesDirty = true;
    }
  }
  if (method === 'web/request') { state.requests.push(p); state.thread.status = 'waiting'; renderRequests(); }
  if (method === 'web/responded') { state.requests = state.requests.filter(r => r.id !== p.id); state.thread.status = 'running'; renderRequests(); }
  if (method === 'error') appendError(p.error?.message || t('Codex 发生错误'));
  scheduleRender();
}

function scheduleThreadRefresh() { clearTimeout(threadRefreshTimer); threadRefreshTimer = setTimeout(() => refreshThreads().catch(e => toast(e.message)), 200); }
async function refreshThreads() {
  const request = ++threadListRequest;
  const result = await api('/threads'); if (request !== threadListRequest) return; state.threads = result.threads;
  if (state.thread) { const t = state.threads.find(t => t.id === state.thread.id); if (t) { state.thread = {...state.thread,...t}; $('chat-title').textContent = t.title; updateRunState(); } }
  renderThreadList();
}
function relativeTime(timestamp) { const age = Date.now()/1000 - timestamp; if (age < 60) return t('刚刚'); if (age < 3600) return t('{count} 分钟', {count: Math.floor(age/60)}); if (age < 86400) return t('{count} 小时', {count: Math.floor(age/3600)}); return new Date(timestamp*1000).toLocaleDateString(uiLanguage,{month:'numeric',day:'numeric'}); }
function renderThreadList() {
  const query = $('search').value.toLowerCase().trim();
  $('thread-count').textContent = state.threads.length;
  const list = $('thread-list'); list.replaceChildren();
  const activePath = state.thread?.cwd || state.settings.cwd;
  const savedPaths = new Set(state.projects.map(project => project.path));
  for (const project of state.projects) {
    const projectMatches = !query || (project.name + ' ' + project.path).toLowerCase().includes(query);
    const threads = state.threads.filter(thread => thread.cwd === project.path && (projectMatches || thread.title.toLowerCase().includes(query)));
    if (!projectMatches && !threads.length) continue;
    const group = document.createElement('section'); group.className = 'project-group'; group.dataset.projectId = project.id;
    const row = document.createElement('div'); row.className = 'project-row' + (activePath === project.path ? ' selected' : '') + (project.available === false ? ' unavailable' : '');
    const toggle = document.createElement('button'); toggle.className = 'project-expand'; toggle.type = 'button';
    const collapsed = !query && collapsedProjects.has(project.id);
    toggle.setAttribute('aria-label', (collapsed ? t('展开 ') : t('收起 ')) + project.name); toggle.setAttribute('aria-expanded', String(!collapsed));
    toggle.innerHTML = '<span aria-hidden="true">›</span>';
    toggle.onclick = () => { if (collapsedProjects.has(project.id)) collapsedProjects.delete(project.id); else collapsedProjects.add(project.id); try { localStorage.setItem('codex-web-collapsed-projects', JSON.stringify([...collapsedProjects])); } catch {} renderThreadList(); };
    const button = document.createElement('button'); button.className = 'project-select'; button.type = 'button'; button.title = project.path;
    button.setAttribute('aria-label', t('选择项目 ') + project.name); button.disabled = project.available === false;
    button.innerHTML = `<svg class="icon" aria-hidden="true"><use href="#icon-folder"/></svg><span>${escapeHTML(project.name)}</span>`;
    button.onclick = () => selectProject(project.id).catch(error => toast(error.message));
    const create = document.createElement('button'); create.className = 'project-new icon-button'; create.type = 'button'; create.textContent = '+';
    create.setAttribute('aria-label', t('在 {name} 中新建对话', {name: project.name})); create.disabled = project.available === false;
    create.onclick = button.onclick;
    const menu = document.createElement('button'); menu.className = 'project-more icon-button'; menu.type = 'button'; menu.textContent = '•••';
    menu.setAttribute('aria-label', project.name + t(' 项目操作')); menu.onclick = () => openProjectMenu(project, menu);
    row.append(toggle, button, create, menu); group.append(row);
    const children = document.createElement('div'); children.className = 'project-threads'; children.hidden = collapsed;
    for (const thread of threads) children.append(threadButton(thread));
    group.append(children); list.append(group);
  }
  const otherThreads = state.threads.filter(thread => !savedPaths.has(thread.cwd) && (!query || thread.title.toLowerCase().includes(query)));
  if (otherThreads.length) {
    if (state.projects.length) { const label = document.createElement('div'); label.className = 'other-threads-label'; label.textContent = t('其他对话'); list.append(label); }
    for (const thread of otherThreads) list.append(threadButton(thread));
  }
  if (!list.children.length) { const p = document.createElement('p'); p.className = 'sidebar-empty'; p.textContent = query ? t('没有找到匹配的对话。') : t('添加一个项目文件夹，\n从这里开始工作。'); list.append(p); }
}
function threadButton(t) {
    const button = document.createElement('button'); button.className = 'thread-item' + (state.thread?.id === t.id ? ' active' : ''); button.title = t.title;
    button.innerHTML = `<span class="thread-icon">${['running','waiting'].includes(t.status) ? '<span class="spinner"></span>' : '○'}</span><span class="thread-text">${escapeHTML(t.title)}</span><span class="thread-time">${relativeTime(t.updated)}</span>`;
    button.onclick = () => selectThread(t.id).catch(e => toast(e.message)); return button;
}
async function refreshProjects() {
  const result = await api('/projects'); state.projects = result.projects; state.settings.cwd = result.cwd;
  applySettings(); renderThreadList();
}
async function selectProject(id) {
  const request = ++projectSwitchRequest;
  const project = state.projects.find(project => project.id === id);
  if (!project || project.available === false) return;
  const previousCwd = state.settings.cwd;
  pendingProjectPath = project.path; state.settings.cwd = project.path; collapsedProjects.delete(id);
  newChat({preserveDraft: true}); closeSidebar();
  const selection = state.selection;
  // Save rapid project changes in click order while the local view responds immediately.
  const saving = projectSaveChain.catch(() => {}).then(() => api('/projects/' + encodeURIComponent(id) + '/select', {}));
  projectSaveChain = saving;
  let result;
  try { result = await saving; }
  catch (error) { if (request === projectSwitchRequest) { pendingProjectPath = null; state.settings.cwd = previousCwd; applySettings(); renderThreadList(); } throw error; }
  if (request !== projectSwitchRequest) return;
  pendingProjectPath = null;
  state.projects = result.projects; state.settings = result.settings;
  applySettings(); renderThreadList(); if (selection === state.selection) updateRunState();
}
function openProjectMenu(project, button) {
  document.querySelector('.project-menu-popover')?.remove();
  const menu = document.createElement('div'); menu.className = 'project-menu-popover';
  const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = t('从列表移除');
  remove.title = t('保留服务器文件和已有对话');
  remove.onclick = async () => {
    remove.disabled = true;
    try { const result = await api('/projects/' + encodeURIComponent(project.id) + '/remove', {}); state.projects = result.projects; state.settings = result.settings; applySettings(); renderThreadList(); menu.remove(); toast(t('已从列表移除，文件和对话已保留')); }
    catch (error) { remove.disabled = false; toast(error.message); }
  };
  menu.append(remove); document.body.append(menu);
  const rect = button.getBoundingClientRect(); menu.style.left = Math.max(8, Math.min(innerWidth - 180, rect.right - 170)) + 'px'; menu.style.top = Math.min(innerHeight - 60, rect.bottom + 4) + 'px';
}
function openProjectDialog() {
  closeSidebar(); $('project-error').textContent = ''; $('project-path').value = state.settings.cwd || '/root';
  $('project-dialog').showModal(); browseDirectories($('project-path').value);
}
async function browseDirectories(path) {
  const request = ++folderBrowseRequest;
  const inputAtStart = $('project-path').value;
  $('project-error').textContent = ''; $('folder-list').textContent = t('正在读取文件夹…'); $('folder-list').setAttribute('aria-busy', 'true');
  try {
    const result = await api('/directories?path=' + encodeURIComponent(path)); if (request !== folderBrowseRequest) return;
    if ($('project-path').value === inputAtStart) $('project-path').value = result.path;
    $('folder-current-path').textContent = result.path; folderParent = result.parent;
    $('folder-up').disabled = !folderParent; $('folder-list').replaceChildren();
    for (const directory of result.directories) {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'folder-entry'; button.title = directory.path;
      button.innerHTML = `<svg class="icon" aria-hidden="true"><use href="#icon-folder"/></svg><span>${escapeHTML(directory.name)}</span><span class="folder-arrow" aria-hidden="true">›</span>`;
      button.onclick = () => browseDirectories(directory.path); $('folder-list').append(button);
    }
    if (!result.directories.length) { const p = document.createElement('p'); p.className = 'folder-empty'; p.textContent = t('此文件夹中没有子文件夹，可以直接添加。'); $('folder-list').append(p); }
    if (result.truncated) { const p = document.createElement('p'); p.className = 'folder-empty'; p.textContent = t('文件夹较多，也可以直接输入目标路径。'); $('folder-list').append(p); }
  } catch (error) {
    if (request === folderBrowseRequest) { $('folder-list').replaceChildren(); $('project-error').textContent = error.message; }
  } finally { if (request === folderBrowseRequest) $('folder-list').setAttribute('aria-busy', 'false'); }
}
function rememberCurrentThread() {
  if (!state.thread || state.loadingThread) return;
  const id = state.thread.id;
  threadCache.delete(id);
  threadCache.set(id, {thread: {...state.thread}, items: [...state.items], turns: [...state.turns],
    requests: [...state.requests], seq: state.threadSeq, hasMore: state.hasMore, before: state.before,
    changePaths: state.changePaths, allChanges: state.allChanges, scrollTop: $('scroll-area').scrollTop,
    stale: false});
  while (threadCache.size > 6) threadCache.delete(threadCache.keys().next().value);
}
function historyControl() {
  let node = $('history-control');
  if (!node) {
    node = document.createElement('div'); node.id = 'history-control'; node.className = 'history-control';
    node.innerHTML = t('<button type="button" id="load-history">加载更早消息</button><span id="history-status" class="muted"></span>');
    $('messages').before(node); $('load-history').onclick = () => loadEarlierMessages().catch(error => toast(error.message));
  }
  node.hidden = !state.hasMore && !state.loadingThread?.blocking && !state.historyLoading;
  $('load-history').hidden = !state.hasMore || !!state.loadingThread?.blocking;
  $('load-history').disabled = !!state.historyLoading || !!state.loadingThread;
  setText($('history-status'), state.loadingThread?.blocking ? t('正在加载对话…') : state.historyLoading ? t('正在加载更早消息…') : '');
}
function displayThread(data, {merge = false, scrollTop = null} = {}) {
  const oldItems = merge ? state.items : [];
  const oldBefore = state.before, oldMore = state.hasMore;
  const ids = new Set(data.items.map(item => item.id));
  state.thread = data.thread; state.items = [...oldItems.filter(item => !ids.has(item.id) && !item.webPending), ...data.items];
  state.turns = data.turns || []; state.requests = data.requests || []; state.threadSeq = data.seq;
  state.hasMore = merge ? oldMore : !!data.hasMore; state.before = merge ? oldBefore : data.before;
  state.changePaths = data.changePaths || []; state.allChanges = data.allChanges || null;
  if (data.serverTime) state.serverOffset = data.serverTime * 1000 - Date.now();
  if (!merge) resetMessageCache(); pinToBottom = scrollTop === null;
  rememberThread(data.thread.id);
  $('chat-title').textContent = data.thread.title; applySettings(); renderThreadList(); renderMessages(); renderRequests(); closeSidebar();
  if (scrollTop !== null) $('scroll-area').scrollTop = scrollTop;
  historyControl();
}
async function selectThread(id, {force = false} = {}) {
  rememberCurrentThread(); navigationController?.abort();
  const selection = ++state.selection;
  const cached = threadCache.get(id);
  if (cached && force) cached.stale = true;
  const loading = {id, events: [], blocking: !cached || cached.stale}; state.loadingThread = loading;
  navigationController = new AbortController(); state.historyLoading = false;
  if (cached) {
    displayThread(cached, {scrollTop: cached.scrollTop});
    for (const event of cached.pendingEvents || []) applyThreadEvent(event.method, event.p, event.eventId, event.tid);
    cached.pendingEvents = []; renderMessages();
  }
  else {
    const thread = state.threads.find(thread => thread.id === id);
    state.thread = thread || {id, status: 'idle', title: t('对话')}; state.items = []; state.turns = []; state.requests = [];
    state.hasMore = false; state.before = null; state.changePaths = []; state.allChanges = null;
    resetMessageCache(); $('chat-title').textContent = state.thread.title;
    applySettings(); renderThreadList(); renderMessages(); renderRequests(); closeSidebar(); historyControl();
  }
  const refresh = async () => {
    let data;
    try { data = await api('/threads/' + id + '?limit=' + HISTORY_PAGE_SIZE, undefined, {signal: navigationController.signal}); }
    catch (error) {
      if (error.name === 'AbortError' || selection !== state.selection) return;
      if (state.loadingThread === loading) { state.loadingThread = null; updateRunState(); historyControl(); }
      throw error;
    }
    if (selection !== state.selection) return;
    state.loadingThread = null;
    const scrollTop = cached ? $('scroll-area').scrollTop : null;
    displayThread(data, {merge: !!cached && !cached.stale, scrollTop});
    for (const event of loading.events) applyThreadEvent(event.method, event.p, event.eventId, event.tid);
    if (loading.events.length) { state.serverOffset = loading.events.at(-1).serverOffset; renderMessages(); }
    rememberCurrentThread();
  };
  if (cached) { refresh().catch(error => toast(error.message)); return; }
  await refresh();
}
async function loadEarlierMessages() {
  if (!state.thread || !state.hasMore || state.historyLoading || state.loadingThread) return;
  const selection = state.selection, id = state.thread.id, before = state.before;
  state.historyLoading = true; historyControl();
  try {
    const data = await api('/threads/' + id + '?limit=' + HISTORY_PAGE_SIZE + '&before=' + before);
    if (selection !== state.selection) return;
    const scroll = $('scroll-area'), height = scroll.scrollHeight, top = scroll.scrollTop;
    const ids = new Set(state.items.map(item => item.id));
    state.items = [...data.items.filter(item => !ids.has(item.id)), ...state.items];
    state.hasMore = !!data.hasMore; state.before = data.before; pinToBottom = false;
    renderMessages(); scroll.scrollTop = top + scroll.scrollHeight - height;
    rememberCurrentThread();
  } finally { if (selection === state.selection) { state.historyLoading = false; historyControl(); } }
}
function newChat({preserveDraft = false} = {}) {
  rememberCurrentThread(); navigationController?.abort();
  if (!preserveDraft) clearAttachments(); state.selection++; state.loadingThread = null;
  state.thread = null; state.items = []; state.turns = []; state.requests = []; state.threadSeq = state.seq;
  state.hasMore = false; state.before = null; state.historyLoading = false; state.changePaths = []; state.allChanges = null;
  // Preserve a deliberately selected new conversation instead of reopening an older project on reload.
  rememberThread('__new_chat__'); $('chat-title').textContent = t('新对话');
  if (!preserveDraft) $('prompt').value = ''; resetMessageCache(); pinToBottom = true;
  applySettings(); renderMessages(); renderRequests(); renderThreadList(); historyControl(); closeSidebar(); $('prompt').focus();
}

function inlineMarkdown(text) {
  let s = escapeHTML(text);
  s = s.replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>').replace(/\*([^*\n]+)\*/g,'<em>$1</em>');
  s = s.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,'<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  return s;
}
function markdown(text) {
  const parts = String(text || '').split(/```/); let html = '';
  parts.forEach((part,index) => {
    if (index % 2) { const newline = part.indexOf('\n'); const lang = newline >= 0 ? part.slice(0,newline).trim() : ''; const code = newline >= 0 ? part.slice(newline+1) : part; html += `<pre><button class="copy-button" type="button">${escapeHTML(t("复制"))}</button><div class="code-label">${escapeHTML(lang || 'CODE')}</div><code>${escapeHTML(code.trimEnd())}</code></pre>`; return; }
    let list = null;
    for (const line of part.split('\n')) {
      const li = line.match(/^\s*([-*]|\d+\.)\s+(.+)/);
      if (li) { const kind = /\d/.test(li[1]) ? 'ol' : 'ul'; if (list !== kind) { if (list) html += `</${list}>`; list = kind; html += `<${kind}>`; } html += `<li>${inlineMarkdown(li[2])}</li>`; continue; }
      if (list) { html += `</${list}>`; list = null; }
      const h = line.match(/^(#{1,3})\s+(.+)/);
      if (h) html += `<h${h[1].length}>${inlineMarkdown(h[2])}</h${h[1].length}>`;
      else if (line.startsWith('> ')) html += `<blockquote>${inlineMarkdown(line.slice(2))}</blockquote>`;
      else if (line.trim()) html += `<p>${inlineMarkdown(line)}</p>`;
    }
    if (list) html += `</${list}>`;
  });
  return html;
}
function itemHTML(item) {
  const id = escapeHTML(item.id);
  if (item.type === 'userMessage') {
    const content = item.content || [];
    const images = content.filter(part => part.type === 'image' || part.type === 'localImage');
    const files = content.filter(part => part.type === 'file');
    const text = content.filter(part => part.type === 'text').map(part => part.text || '').join('\n');
    const thumbnails = images.map(image => {
      const url = safeImageURL(image.url);
      return url ? `<button class="message-image" type="button" data-image-url="${escapeHTML(url)}" data-image-name="${escapeHTML(image.name || t('图片'))}" aria-label="${escapeHTML(t("查看图片 "))}${escapeHTML(image.name || '')}"><img src="${escapeHTML(url)}" alt="${escapeHTML(image.name || t('图片附件'))}" loading="lazy"></button>` : t('<span class="missing-image">图片附件</span>');
    }).join('');
    const documents = files.map(file => safeImageURL(file.url) ? `<button type="button" class="message-file" data-file-id="${escapeHTML(file.id || file.attachmentId)}"><span class="file-symbol">▤</span><span><strong>${escapeHTML(file.name || t('文件'))}</strong><small>${escapeHTML(fileSize(file.size))}</small></span></button>` : t('<span class="missing-image">文件附件</span>')).join('');
    return `<article class="message user" data-item-id="${id}"><div class="user-bubble${images.length || files.length ? ' has-images' : ''}">${images.length ? '<div class="message-images">' + thumbnails + '</div>' : ''}${files.length ? '<div class="message-files">' + documents + '</div>' : ''}${text ? '<div class="user-text">' + escapeHTML(text) + '</div>' : ''}</div></article>`;
  }
  if (item.type === 'agentMessage') return `<article class="message assistant ${item.phase === 'commentary' ? 'commentary' : ''}" data-item-id="${id}"><div class="markdown">${markdown(item.text)}</div></article>`;
  if (item.type === 'commandExecution') return `<details class="tool" data-item-id="${id}"><summary><span>${item.status === 'inProgress' ? '◌' : item.exitCode && item.exitCode !== 0 ? '!' : '✓'}</span><strong>${escapeHTML(t("执行命令"))}</strong><span>${escapeHTML((item.command || '').slice(0,95))}</span></summary><div class="tool-cwd">${escapeHTML(item.cwd || '')} ${item.exitCode != null ? t(' · 退出码 ')+escapeHTML(item.exitCode) : ''}</div><pre></pre></details>`;
  if (item.type === 'fileChange') return `<details class="tool" data-item-id="${id}"><summary><span>✓</span><strong>${escapeHTML(t("文件变更"))}</strong><span>${escapeHTML((item.changes || []).map(c => c.path.split('/').at(-1)).join(', '))}</span></summary><pre class="diff"></pre></details>`;
  if (item.type === 'reasoning') {
    const text = item.summaryText || (item.summary || []).join('\n');
    return `<details class="tool reasoning" data-item-id="${id}"><summary><span class="reasoning-symbol">✧</span><strong data-reasoning-id="${id}">${escapeHTML(t("思考"))}</strong><span class="reasoning-preview">${escapeHTML(text.split('\n').find(Boolean) || t('正在分析任务'))}</span></summary><div class="reasoning-content"><p class="muted">${escapeHTML(t("展开查看思考摘要。"))}</p></div></details>`;
  }
  if (item.type === 'plan') return `<article class="message"><div class="assistant-label"><span>☷</span>${escapeHTML(t(" 工作计划"))}</div><div class="markdown">${markdown(item.text || '')}</div></article>`;
  if (item.type === 'mcpToolCall') return `<details class="tool" data-item-id="${id}"><summary><span>◇</span><strong>${escapeHTML(t("调用工具"))}</strong><span>${escapeHTML(item.server || '')} / ${escapeHTML(item.tool || '')}</span></summary><pre></pre></details>`;
  if (item.type === 'webSearch') return `<details class="tool" data-item-id="${id}"><summary><span>⌕</span><strong>${escapeHTML(t("搜索"))}</strong><span>${escapeHTML(item.query || '')}</span></summary></details>`;
  return '';
}
function scheduleRender() { if (renderFrame) return; renderFrame = setTimeout(() => { renderFrame = null; requestAnimationFrame(renderMessages); }, 40); }
function renderToolBody(node, item) {
  if (!node.open) return;
  if (item.type === 'reasoning') {
    const text = item.summaryText || (item.summary || []).join('\n');
    node.querySelector('.reasoning-content').innerHTML = text ? markdown(text) : t('<p class="muted">当前模型未提供思考摘要。</p>');
  } else if (item.type === 'commandExecution') node.querySelector('pre').textContent = item.aggregatedOutput || t('等待输出…');
  else if (item.type === 'fileChange') node.querySelector('pre').textContent = (item.changes || []).map(change => change.path + '\n' + (change.diff || '')).join('\n\n');
  else if (item.type === 'mcpToolCall') node.querySelector('pre').textContent = JSON.stringify(item.result || item.arguments || {}, null, 2);
}
function resetMessageCache() { messageNodes.clear(); messageVersions.clear(); dirtyItems.clear(); $('messages').replaceChildren(); changesVersion = ''; changesDirty = true; }
function renderMessages() {
  const scroll = $('scroll-area');
  const threadKey = state.thread?.id || 'new';
  if (renderedThread !== threadKey) { resetMessageCache(); renderedThread = threadKey; }
  $('welcome').hidden = state.items.length > 0 || !!state.loadingThread?.blocking;
  const liveIds = new Set([...state.items.map(item => item.id), ...state.turns.map(turn => 'turn:' + turn.id)]);
  for (const [id, node] of messageNodes) if (!liveIds.has(id)) { node.remove(); messageNodes.delete(id); messageVersions.delete(id); }
  let previousNode = null;
  for (const item of state.items) {
    if (messageVersions.get(item.id) === item && !dirtyItems.has(item.id)) { previousNode = messageNodes.get(item.id) || previousNode; continue; }
    const html = itemHTML(item);
    let node = messageNodes.get(item.id);
    if (!html) continue;
    if (!node) {
      const template = document.createElement('template'); template.innerHTML = html; node = template.content.firstElementChild;
      messageNodes.set(item.id, node); if (previousNode) previousNode.after(node); else $('messages').prepend(node);
    } else if (item.type === 'agentMessage') {
      node.classList.toggle('commentary', item.phase === 'commentary');
      node.querySelector('.markdown').innerHTML = markdown(item.text);
    } else if (item.type === 'reasoning') {
      const text = item.summaryText || (item.summary || []).join('\n');
      node.querySelector('.reasoning-preview').textContent = text.split('\n').find(Boolean) || t('正在分析任务');
    } else if (item.type === 'commandExecution') {
      node.querySelector('summary > span').textContent = item.status === 'inProgress' ? '◌' : item.exitCode && item.exitCode !== 0 ? '!' : '✓';
      node.querySelector('.tool-cwd').textContent = (item.cwd || '') + (item.exitCode != null ? t(' · 退出码 ') + item.exitCode : '');
    } else {
      const template = document.createElement('template'); template.innerHTML = html;
      const replacement = template.content.firstElementChild; if (node.open) replacement.open = true;
      node.replaceWith(replacement); messageNodes.set(item.id, replacement);
      node = replacement;
    }
    renderToolBody(node, item); previousNode = node;
    messageVersions.set(item.id, item);
  }
  dirtyItems.clear();
  renderTurnTimings();
  updateRunState(); renderChanges();
  if (pinToBottom) scroll.scrollTop = scroll.scrollHeight;
}
function durationLabel(milliseconds) {
  const seconds = Math.floor(Math.max(0, milliseconds) / 1000);
  if (seconds < 1) return t('不足 1 秒');
  return seconds < 60 ? t('{seconds} 秒', {seconds}) : t('{minutes} 分 {seconds} 秒', {minutes: Math.floor(seconds / 60), seconds: String(seconds % 60).padStart(2, '0')});
}
function serverNow() { return Date.now() + state.serverOffset; }
function reasoningDuration(item, turnsById) {
  const timing = item.webTiming; if (!timing) return null;
  if (timing.measurement === 'unavailable') return null;
  const turn = turnsById ? turnsById.get(item.webTurnId) : state.turns.find(t => t.id === item.webTurnId);
  const end = timing.completedAt || turn?.completedAt;
  // Apply the same rule to existing history, which has no measurement marker.
  if (end && !timing.measurement && !timing.streamed && !item.summaryText && !(item.summary || []).some(Boolean) && end - timing.startedAt < 1) return null;
  return end ? Math.max(0, (end - timing.startedAt) * 1000) : Math.max(0, serverNow() - timing.startedAt * 1000);
}
function renderTurnTimings() {
  const turnsById = new Map(state.turns.map(turn => [turn.id, turn]));
  const grouped = new Map();
  for (const item of state.items) { if (!grouped.has(item.webTurnId)) grouped.set(item.webTurnId, []); grouped.get(item.webTurnId).push(item); }
  for (const turn of state.turns) {
    let node = messageNodes.get('turn:' + turn.id);
    const items = grouped.get(turn.id) || [];
    const anchor = (turn.completedAt && [...items].reverse().find(item => item.type === 'agentMessage' && item.phase !== 'commentary')) || items.find(item => item.type !== 'userMessage');
    if (!anchor || !messageNodes.has(anchor.id)) continue;
    if (!node) { node = document.createElement('div'); node.className = 'turn-timing'; node.dataset.turnId = turn.id; messageNodes.set('turn:' + turn.id, node); }
    if (node.nextElementSibling !== messageNodes.get(anchor.id)) messageNodes.get(anchor.id).before(node);
    if (turn.completedAt) {
      const reasoningItems = items.filter(item => item.type === 'reasoning');
      const intervals = reasoningItems.filter(item => reasoningDuration(item, turnsById) !== null).map(item => [item.webTiming.startedAt, item.webTiming.completedAt || turn.completedAt]).sort((a, b) => a[0] - b[0]);
      let reasoning = 0, end = 0;
      for (const [start, stop] of intervals) { reasoning += Math.max(0, stop - Math.max(start, end)) * 1000; end = Math.max(end, stop); }
      const unavailable = reasoningItems.some(item => reasoningDuration(item, turnsById) === null);
      const status = turn.status === 'interrupted' ? t('已停止') : turn.status === 'failed' ? t('任务失败') : t('已完成');
      setText(node, `${status}${t(' · 耗时 ')}${durationLabel((turn.completedAt - turn.startedAt) * 1000)}${reasoning ? ' · ' + (unavailable ? t('已记录思考 ') : t('思考 ')) + durationLabel(reasoning) : ''}${unavailable ? ' · ' + t(reasoning ? '部分思考耗时未提供' : '思考耗时未提供') : ''}`);
    } else setText(node, t('任务进行中'));
  }
  updateClocks();
}
function updateClocks() {
  const turnsById = new Map(state.turns.map(turn => [turn.id, turn]));
  for (const item of state.items) if (item.type === 'reasoning') {
    const label = messageNodes.get(item.id)?.querySelector('[data-reasoning-id]');
    if (!label) continue;
    const ms = reasoningDuration(item, turnsById);
    const turn = turnsById.get(item.webTurnId);
    const completed = item.webTiming?.completedAt || turn?.completedAt;
    setText(label, ms === null ? (completed ? t('思考完成') : t('思考摘要')) : (completed ? t('已思考 ') : t('正在思考 ')) + durationLabel(ms));
    const text = item.summaryText || (item.summary || []).join('\n');
    if (!text) {
      const node = messageNodes.get(item.id);
      setText(node.querySelector('.reasoning-preview'), completed ? (ms === null ? t('耗时未提供') : t('未提供思考摘要')) : t('正在分析任务'));
      setText(node.querySelector('.reasoning-content p'), completed && ms === null ? t('模型未提供可单独计量的思考耗时。任务总用时和等待回复时间会继续显示。') : t('当前模型未提供思考摘要。'));
    }
  }
  const turn = state.turns.find(t => t.id === state.thread?.turn_id) || state.turns.at(-1);
  const items = state.items.filter(item => item.webTurnId === turn?.id);
  const active = [...items].reverse().find(item => item.type !== 'userMessage' && item.webTiming && !item.webTiming.completedAt);
  const waiting = turn && !turn.completedAt && !active && state.thread?.status !== 'waiting';
  const lastOutputAt = Math.max(turn?.startedAt || 0, ...items.map(item => item.webTiming?.completedAt || item.webTiming?.startedAt || 0));
  setText($('working-label'), state.sending && !turn ? t('正在发送任务') : active?.type === 'reasoning' ? t('正在思考') : active?.type === 'commandExecution' ? t('正在执行命令') : waiting ? t('正在思考 / 等待回复') : t('Codex 正在工作'));
  setText($('working-time'), turn && !turn.completedAt ? (waiting ? t('已等待 ') + durationLabel(serverNow() - lastOutputAt * 1000) + ' · ' : '') + t('已用时 ') + durationLabel(serverNow() - turn.startedAt * 1000) : '');
}

function appendError(message) { message = translateError(message); const node = document.createElement('p'); node.className = 'error-message'; node.textContent = message; $('messages').append(node); }
function updateRunState() {
  const status = state.thread?.status || 'idle'; const running = ['running','waiting'].includes(status);
  $('run-status').textContent = status === 'running' ? t('运行中') : status === 'waiting' ? t('等待你的确认') : status === 'failed' ? t('任务失败') : status === 'interrupted' ? t('已停止') : t('就绪');
  $('run-status').className = 'status-pill' + (running ? ' '+status : '');
  $('working-indicator').hidden = (!running && !state.sending) || status === 'waiting';
  $('stop-button').hidden = !running; $('stop-button').disabled = !state.thread?.turn_id;
  const imagesReady = state.attachments.length > 0 && state.attachments.every(image => image.status === 'ready');
  const imagesPending = state.attachments.some(image => image.status !== 'ready');
  $('send-button').hidden = running; $('send-button').disabled = !state.csrf || !!state.loadingThread?.blocking || (!$('prompt').value.trim() && !imagesReady) || imagesPending || state.sending;
  $('attach-image').disabled = !state.csrf || state.sending || state.attachments.length >= MAX_IMAGES;
  updateClocks();
}
function renderChanges() {
  if (!changesDirty) return; changesDirty = false;
  const loadedChanges = state.items.filter(item => item.type === 'fileChange').flatMap(item => item.changes || []);
  const paths = new Set([...(state.changePaths || []), ...(state.allChanges || loadedChanges).map(change => change.path)]);
  $('change-count').textContent = paths.size;
  if ($('changes-panel').hidden) return;
  if (!Array.isArray(state.allChanges) && state.thread) {
    const selection = state.selection, id = state.thread.id, request = ++changesRequest;
    $('changes-body').textContent = t('正在加载文件变更…');
    api('/threads/' + id + '/changes').catch(async error => {
      if (error.status !== 404) throw error;
      const data = await api('/threads/' + id); return {changes: data.items.filter(item => item.type === 'fileChange').flatMap(item => item.changes || [])};
    }).then(data => {
      if (selection !== state.selection || request !== changesRequest) return;
      state.allChanges = data.changes; changesDirty = true; renderChanges();
    }).catch(error => { if (selection === state.selection) $('changes-body').textContent = error.message; });
    return;
  }
  const changes = state.allChanges || loadedChanges;
  const version = JSON.stringify(changes); if (version === changesVersion) return; changesVersion = version;
  $('changes-body').innerHTML = changes.length ? changes.map(c => `<article class="file-card"><div class="file-card-header"><span>▤</span><strong>${escapeHTML(c.path)}</strong><button class="secondary preview-file" data-path="${escapeHTML(c.path)}">${escapeHTML(t("预览"))}</button></div><pre>${(c.diff || '').split('\n').map(line => `<div class="diff-line ${line.startsWith('+') ? 'add' : line.startsWith('-') ? 'remove' : ''}">${escapeHTML(line)}</div>`).join('')}</pre></article>`).join('') : t('<p class="muted">当前对话还没有文件变更。</p>');
}

function renderRequests() {
  $('requests').replaceChildren();
  for (const request of state.requests) {
    const p = request.params || {}, card = document.createElement('section'); card.className = 'request-card';
    if (request.method === 'item/tool/requestUserInput') {
      card.innerHTML = t('<h3>Codex 需要你的回答</h3>');
      for (const q of p.questions || []) {
        const label = document.createElement('label'); label.textContent = q.question;
        const input = q.options?.length ? document.createElement('select') : document.createElement('input'); input.dataset.questionId = q.id;
        if (q.options?.length) { input.add(new Option(t('选择一个回答'),'')); for (const opt of q.options) input.add(new Option(opt.label+(opt.description ? ' · '+opt.description : ''),opt.label)); input.add(new Option(t('自定义回答'),'__custom__')); }
        label.append(input);
        const custom = document.createElement('input'); custom.placeholder = t('输入你的回答'); custom.hidden = !!q.options?.length; custom.dataset.customFor = q.id;
        if (q.options?.length) { label.append(custom); input.onchange = () => custom.hidden = input.value !== '__custom__'; }
        card.append(label);
      }
      const button = document.createElement('button'); button.className = 'primary request-actions'; button.textContent = t('提交回答');
      button.onclick = async () => { const answers = {}; for (const input of card.querySelectorAll('[data-question-id]')) { const value = input.value === '__custom__' ? [...card.querySelectorAll('[data-custom-for]')].find(c => c.dataset.customFor === input.dataset.questionId).value : input.value; if (!value.trim()) { toast(t('请回答所有问题')); return; } answers[input.dataset.questionId] = {answers:[value]}; } await respond(request, {answers}, button); };
      card.append(button);
    } else {
      const supported = ['item/commandExecution/requestApproval','item/fileChange/requestApproval','item/permissions/requestApproval'].includes(request.method);
      card.innerHTML = `<h3>${supported ? t('需要你的批准') : t('此工具请求暂不支持')}</h3><p>${escapeHTML(p.reason || (supported ? t('查看操作内容，决定是否继续。') : request.method))}</p><pre>${escapeHTML(p.command || JSON.stringify(p.permissions || p.changes || p, null,2))}</pre>`;
      const actions = document.createElement('div'); actions.className = 'request-actions';
      for (const [label,decision] of (supported ? [[t('批准本次'),'accept'],[t('拒绝'),'decline']] : [[t('跳过请求'),'decline']])) { const button = document.createElement('button'); button.className = decision === 'accept' ? 'primary' : 'secondary'; button.textContent = label; button.onclick = () => respond(request, {decision},button); actions.append(button); }
      card.append(actions);
    }
    $('requests').append(card);
  }
}
async function respond(request, result, button) {
  button.disabled = true;
  try { await api('/respond',{id:request.id,...result}); state.requests = state.requests.filter(r => r.id !== request.id); renderRequests(); } catch (e) { toast(e.message); button.disabled = false; }
}
function safeImageURL(url) { return typeof url === 'string' && /^\/api\/attachments\/[a-f0-9]{32}$/.test(url) ? url : ''; }
function fileSize(size) { return size >= 1024 * 1024 ? (size / (1024 * 1024)).toFixed(1) + ' MB' : Math.max(1, Math.ceil((size || 0) / 1024)) + ' KB'; }
let filePreviewRequest = 0;
async function previewFile(id) {
  if (!/^[a-f0-9]{32}$/.test(id)) return;
  const request = ++filePreviewRequest;
  $('file-dialog-title').textContent = t('文件预览'); $('file-preview-text').textContent = t('正在读取文件…');
  $('file-preview-pages').replaceChildren(); $('file-preview-note').textContent = ''; $('file-download').hidden = true;
  $('file-dialog').showModal();
  try {
    const data = await api('/attachments/' + id + '/preview');
    if (request !== filePreviewRequest || !$('file-dialog').open) return;
    $('file-dialog-title').textContent = data.attachment.name;
    $('file-preview-text').textContent = data.text || (data.pages.length ? t('以下为文档页面预览。') : t('此文件暂无文本预览，可下载原文件或让 Codex 分析。'));
    $('file-preview-note').textContent = t(data.attachment.note || '') || (data.truncated ? t('预览展示部分内容，原文件可完整下载。') : fileSize(data.attachment.size));
    $('file-download').href = safeImageURL(data.attachment.url); $('file-download').download = data.attachment.name; $('file-download').hidden = false;
    for (const page of data.pages) if (new RegExp('^/api/attachments/' + id + '/pages/\\d+$').test(page.url)) {
      const image = document.createElement('img'); image.src = page.url; image.alt = t('第 {number} 页', {number: page.number}); image.loading = 'lazy'; $('file-preview-pages').append(image);
    }
  } catch (error) { if (request === filePreviewRequest) $('file-preview-text').textContent = error.message; }
}
function renderAttachments() {
  const container = $('composer-attachments'); container.replaceChildren(); container.hidden = !state.attachments.length;
  for (const image of state.attachments) {
    const tile = document.createElement('div'); tile.className = 'attachment-tile ' + image.status + (image.kind === 'file' ? ' file-tile' : ''); tile.title = image.name;
    let preview;
    if (image.kind === 'file') {
      preview = document.createElement('button'); preview.type = 'button'; preview.className = 'file-tile-preview';
      preview.textContent = '▤ ' + (image.name.split('.').at(-1) || 'FILE').toUpperCase().slice(0,8);
      preview.setAttribute('aria-label', t('预览文件 ') + image.name); preview.disabled = image.status !== 'ready';
      preview.onclick = () => previewFile(image.id);
    } else {
      preview = document.createElement('img'); preview.src = image.previewURL; preview.alt = image.name;
      preview.onclick = () => { $('image-viewer-image').src = image.previewURL; $('image-dialog-title').textContent = image.name; $('image-dialog').showModal(); };
    }
    if (image.phase === 'confirming') tile.title += '\n' + t(image.kind === 'file' ? '文件仍在传输或等待服务器处理，尚未完成上传。' : '图片仍在传输或等待服务器确认，尚未完成上传。');
    tile.append(preview);
    const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'attachment-remove'; remove.textContent = '×';
    remove.onclick = () => removeAttachment(image.clientId); remove.setAttribute('aria-label', t(image.kind === 'file' ? '移除文件 {name}' : '移除图片 {name}', {name: image.name})); tile.append(remove);
    const caption = document.createElement('span'); caption.className = 'attachment-caption'; caption.textContent = attachmentCaption(image); tile.append(caption);
    image.caption = caption;
    if (image.savedBytes) tile.title += t('\n已减少 ') + Math.round(image.savedBytes / image.file.size * 100) + t('% 上传流量，保留像素尺寸');
    if (image.status === 'error') {
      const retry = document.createElement('button'); retry.type = 'button'; retry.className = 'attachment-retry'; retry.textContent = t('重试'); retry.title = image.error || t('重新上传图片');
      retry.onclick = () => uploadImage(image); tile.append(retry);
    }
    container.append(tile);
  }
  updateRunState();
}
function attachmentCaption(image) {
  if (image.status === 'error') return t('上传失败');
  if (image.status === 'ready') return image.name;
  if (image.phase === 'queued') return t('等待上传…');
  if (image.phase === 'preparing') return t('优化图片…');
  if (image.phase === 'confirming') return t('等待确认 {seconds} 秒', {seconds: Math.floor(Math.max(0, Date.now() - image.confirmingAt) / 1000)});
  if (image.phase === 'processing') return image.kind === 'file' ? t('解析文件…') : t('校验图片…');
  return t('上传 ') + (image.progress || 0) + '%';
}
function updateUploadCaption(image) { if (image.caption) image.caption.textContent = attachmentCaption(image); }
function prepareImageUpload(image, signal) {
  if (image.kind !== 'image' || image.original || image.file.size < 256 * 1024 || !window.Worker) return Promise.resolve(image.file);
  return new Promise(resolve => {
    let worker, timer;
    const finish = blob => { clearTimeout(timer); worker?.terminate(); signal.removeEventListener('abort', aborted); resolve(blob); };
    const aborted = () => finish(image.file);
    try {
      worker = new Worker('/image-upload-worker.js');
      worker.onmessage = event => finish(event.data);
      worker.onerror = () => finish(image.file);
      signal.addEventListener('abort', aborted, {once:true});
      timer = setTimeout(() => finish(image.file), 8000);
      worker.postMessage(image.file);
    } catch { finish(image.file); }
  });
}
function transferAttachment(image, blob, signal) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    let settled = false, deadline, ticker;
    const aborted = () => xhr.abort();
    const finish = (error, value) => {
      if (settled) return;
      settled = true; clearTimeout(deadline); clearInterval(ticker);
      signal.removeEventListener('abort', aborted);
      error ? reject(error) : resolve(value);
    };
    xhr.open('POST', '/api/attachments?name=' + encodeURIComponent(image.name) + (image.kind === 'file' ? '&kind=file' : ''));
    xhr.timeout = 120000;
    xhr.setRequestHeader('Content-Type', blob.type || 'application/octet-stream');
    xhr.setRequestHeader('X-CSRF-Token', state.csrf);
    xhr.upload.onprogress = event => {
      if (settled || !event.lengthComputable) return;
      image.progress = Math.min(99, Math.round(event.loaded / event.total * 100));
      // Browser progress measures bytes handed to the network, not receipt by the server.
      if (event.loaded === event.total && image.phase !== 'confirming') {
        image.phase = 'confirming'; image.confirmingAt = Date.now(); renderAttachments();
      }
      updateUploadCaption(image);
    };
    xhr.onload = () => {
      let result;
      try { result = JSON.parse(xhr.responseText); if (!result || typeof result !== 'object') throw new Error(); } catch { finish(new Error(t('服务器返回了无效响应'))); return; }
      if (xhr.status < 200 || xhr.status >= 300) { if (xhr.status === 401) showAuth(false); finish(new Error(translateError(result.error || '附件上传失败'))); }
      else if (!result.attachment || !/^[a-f0-9]{32}$/.test(result.attachment.id || '') || !safeImageURL(result.attachment.url)) finish(new Error(t('服务器返回了无效响应')));
      else finish(null, result);
    };
    xhr.onerror = () => finish(new Error(t('网络连接中断，请重试上传')));
    xhr.ontimeout = () => finish(new Error(t('上传超时，请检查网络后重试')));
    xhr.onabort = () => finish(new DOMException(t('上传已取消'), 'AbortError'));
    signal.addEventListener('abort', aborted, {once:true});
    if (signal.aborted) { finish(new DOMException(t('上传已取消'), 'AbortError')); return; }
    // Bound the wait even if a browser fails to dispatch its native timeout event.
    deadline = setTimeout(() => { finish(new Error(t('上传超时，请检查网络后重试'))); xhr.abort(); }, 120000);
    ticker = setInterval(() => { if (image.phase === 'confirming') updateUploadCaption(image); }, 1000);
    try { xhr.send(blob); } catch (error) { finish(error); }
  });
}
function uploadImage(image) {
  if (uploadQueue.includes(image) || image.uploadActive) return;
  image.status = 'uploading'; image.phase = 'queued'; image.progress = 0;
  uploadQueue.push(image); renderAttachments(); drainUploads();
}
function drainUploads() {
  while (activeUploads < 2 && uploadQueue.length) {
    const image = uploadQueue.shift();
    if (!state.attachments.includes(image)) continue;
    activeUploads++; image.uploadActive = true;
    performUpload(image).finally(() => { activeUploads--; image.uploadActive = false; drainUploads(); });
  }
}
async function performUpload(image) {
  image.phase = 'preparing'; image.controller = new AbortController(); updateUploadCaption(image);
  try {
    const signal = image.controller.signal;
    const blob = image.uploadBlob || await prepareImageUpload(image, signal);
    if (signal.aborted || !state.attachments.includes(image)) return;
    image.uploadBlob = blob; image.savedBytes = image.file.size - blob.size;
    image.phase = 'transferring'; updateUploadCaption(image);
    const result = await transferAttachment(image, blob, signal);
    if (!state.attachments.includes(image)) { api('/attachments/' + result.attachment.id + '/remove', {}).catch(() => {}); return; }
    Object.assign(image, result.attachment); image.status = 'ready';
  } catch (error) {
    if (error.name === 'AbortError' || !state.attachments.includes(image)) return;
    image.status = 'error'; image.error = error.message; toast(error.message);
  } finally { if (state.attachments.includes(image)) renderAttachments(); }
}
function addImageFiles(files) {
  if (!state.csrf || state.sending) return;
  for (const file of files) {
    if (state.attachments.length >= MAX_IMAGES) { toast(t('每条消息最多添加 8 个附件')); break; }
    const isImage = ['image/png', 'image/jpeg', 'image/webp', 'image/gif'].includes(file.type) || /\.(png|jpe?g|webp|gif)$/i.test(file.name);
    if (!file.size || file.size > (isImage ? MAX_IMAGE_BYTES : MAX_FILE_BYTES)) { toast(isImage ? t('每张图片最大 10 MB') : t('每个文件最大 25 MB')); continue; }
    const image = {clientId: 'image-' + ++imageSequence, kind: isImage ? 'image' : 'file', file, name: file.name || t('粘贴的图片.png'), previewURL: isImage ? URL.createObjectURL(file) : '', status: 'uploading', original: $('original-image').checked};
    state.attachments.push(image); uploadImage(image);
  }
  renderAttachments();
}
function removeAttachment(clientId) {
  const image = state.attachments.find(value => value.clientId === clientId); if (!image) return;
  state.attachments = state.attachments.filter(value => value !== image); const queued = uploadQueue.indexOf(image); if (queued >= 0) uploadQueue.splice(queued, 1); image.controller?.abort(); URL.revokeObjectURL(image.previewURL);
  if (image.id && state.csrf) api('/attachments/' + image.id + '/remove', {}).catch(() => {});
  renderAttachments();
}
function clearAttachments() { for (const image of [...state.attachments]) removeAttachment(image.clientId); }
async function sendMessage(event) {
  event.preventDefault(); const text = $('prompt').value.trim(); const images = [...state.attachments];
  if ((!text && !images.length) || images.some(image => image.status !== 'ready') || state.sending || state.loadingThread?.blocking || ['running','waiting'].includes(state.thread?.status)) return;
  const selection = state.selection;
  const pendingId = 'pending:' + Date.now();
  state.items.push({id: pendingId, type: 'userMessage', content: [...(text ? [{type: 'text', text}] : []), ...images.map(image => ({type: image.kind || 'image', ...image, file: undefined, uploadBlob: undefined, caption: undefined, controller: undefined}))], webPending: true});
  state.attachments = []; renderAttachments();
  $('prompt').value = ''; $('prompt').style.height = '';
  state.sending = true; pinToBottom = true; renderMessages();
  let targetThread = state.thread;
  const targetCwd = targetThread?.cwd || state.settings.cwd;
  const skill = selectedSkill && selectedSkill.cwd === targetCwd && text.includes('$' + selectedSkill.name) ? selectedSkill : null;
  try {
    if (!targetThread) {
      const result = await api('/threads',{cwd: targetCwd}); targetThread = result.thread;
      if (selection === state.selection) {
        state.thread = targetThread; state.threadSeq = state.seq;
        // Keep the optimistic message when the server assigns the new thread ID.
        renderedThread = targetThread.id;
        rememberThread(targetThread.id); applySettings();
      }
    }
    const tid = targetThread.id;
    await api('/threads/'+tid+'/send',{text, attachments: images.map(image => image.id), ...(skill ? {skills: [skill.path]} : {})});
    if (selectedSkill === skill) selectedSkill = null;
    for (const image of images) URL.revokeObjectURL(image.previewURL);
    scheduleThreadRefresh();
    if (selection === state.selection && state.items.some(item => item.id === pendingId)) {
      // A disconnected stream needs a snapshot; ordinary sends use live events.
      if (state.stream?.readyState !== EventSource.OPEN) await selectThread(tid).catch(error => toast(t('消息已发送，历史暂未加载：') + error.message));
    }
  } catch (e) {
    toast(e.message);
    if (selection === state.selection) {
      state.items = state.items.filter(item => item.id !== pendingId);
      if (!$('prompt').value) $('prompt').value = text;
      state.attachments = [...images, ...state.attachments]; renderAttachments();
      renderMessages();
    } else {
      for (const image of images) URL.revokeObjectURL(image.previewURL);
    }
    if (state.thread) refreshThreads().catch(() => {});
  }
  finally { state.sending = false; updateRunState(); }
}
function closeSidebar() { $('sidebar').classList.remove('open'); $('sidebar-backdrop').hidden = true; }
function openSettings(tab='general') {
  const s = state.settings;
  $('setting-cwd').value = s.cwd; $('setting-model').value = s.model; $('setting-effort').value = s.effort; $('setting-sandbox').value = s.sandbox; $('setting-approval').value = s.approvalPolicy; $('setting-theme').value = s.theme;
  $('credentials-form').reset(); $('setting-username').value = state.username;
  $('general-error').textContent = ''; $('credentials-error').textContent = ''; selectSettingsTab(tab);
  closeSidebar(); $('settings-dialog').showModal();
}
function selectSettingsTab(tab) {
  for (const el of document.querySelectorAll('[data-panel]')) el.hidden = el.dataset.panel !== tab;
  for (const el of document.querySelectorAll('[data-tab]')) el.classList.toggle('active',el.dataset.tab === tab);
  if (tab === 'extensions') loadExtensions();
}
let extensionData = null, extensionLoading = false, extensionRequest = 0, extensionMutating = false, selectedSkill = null;
async function loadExtensions(refresh = false) {
  const cwd = state.thread?.cwd || state.settings.cwd;
  const request = ++extensionRequest;
  extensionLoading = true; extensionData = null; renderExtensions();
  try {
    const data = await api('/extensions?cwd=' + encodeURIComponent(cwd) + (refresh ? '&refresh=1' : ''));
    if (request === extensionRequest) extensionData = data;
  } catch (error) {
    if (request === extensionRequest) extensionData = {cwd, error: error.status === 404 ? '插件功能正在更新，请等当前任务完成后刷新网页' : error.message};
  } finally {
    if (request === extensionRequest) { extensionLoading = false; renderExtensions(); }
  }
}
function renderExtensions() {
  const container = $('extensions-list'); if (!container) return;
  container.replaceChildren();
  $('refresh-extensions').disabled = extensionLoading || extensionMutating;
  const cwd = extensionData?.cwd || state.thread?.cwd || state.settings.cwd || '';
  $('extensions-project').textContent = t('当前项目：{name}', {name: cwd.split('/').filter(Boolean).at(-1) || '/'});
  $('extensions-project').title = cwd;
  $('extensions-status').textContent = extensionLoading ? t('正在加载插件与技能…') : translateError(extensionData?.error || '');
  if (!extensionData || extensionData.error) return;
  for (const [kind, title, empty] of [['plugins', '已安装插件', '尚未安装插件，可先在服务器上安装，再刷新列表。'], ['skills', '可用技能', '当前项目没有发现技能。']]) {
    const heading = document.createElement('h4'); heading.textContent = t(title); container.append(heading);
    const section = extensionData[kind];
    if (!section || section.error || !section.items?.length) {
      const notice = document.createElement('p'); notice.className = 'muted'; notice.textContent = translateError(section?.error || t(empty)); container.append(notice); continue;
    }
    if (section.warningCount) { const notice = document.createElement('p'); notice.className = 'muted'; notice.textContent = t('部分插件或技能未能加载，请检查服务器配置后刷新。'); container.append(notice); }
    for (const item of section.items) {
      const card = document.createElement('article'); card.className = 'extension-card';
      const title = document.createElement('strong'); title.textContent = item.displayName || item.name; card.append(title);
      const description = document.createElement('p'); description.textContent = item.description; card.append(description);
      const meta = document.createElement('small'); meta.textContent = [kind === 'plugins' ? item.marketplace : item.name, item.version, t(item.available === false ? '暂不可用' : item.enabled ? '已启用' : '已禁用')].filter(Boolean).join(' · '); card.append(meta);
      const actions = document.createElement('div'); actions.className = 'extension-actions';
      const toggle = document.createElement('button'); toggle.type = 'button'; toggle.className = 'secondary';
      toggle.textContent = t(item.enabled ? '禁用' : '启用'); toggle.disabled = extensionMutating || (!item.enabled && item.available === false);
      toggle.setAttribute('aria-label', t(item.enabled ? '禁用' : '启用') + ' ' + item.name);
      toggle.onclick = async () => {
        if (extensionMutating) return;
        extensionMutating = true; renderExtensions();
        try {
          await api('/extensions/' + (kind === 'plugins' ? 'plugin' : 'skill'), {cwd: extensionData.cwd, enabled: !item.enabled, ...(kind === 'plugins' ? {id: item.id} : {path: item.path})});
          toast(t('设置已保存，建议在新对话中使用')); await loadExtensions(true);
        } catch (error) { toast(error.message); }
        finally { extensionMutating = false; renderExtensions(); }
      };
      actions.append(toggle);
      if (kind === 'skills') {
        const use = document.createElement('button'); use.type = 'button'; use.className = 'secondary'; use.textContent = t('在对话中使用'); use.disabled = !item.enabled || state.sending || extensionMutating;
        use.onclick = () => {
          selectedSkill = {...item, cwd: extensionData.cwd};
          const draft = $('prompt').value.trim(); const mention = '$' + item.name;
          $('prompt').value = (draft.includes(mention) ? draft : mention + ' ' + (draft || item.defaultPrompt || t('请使用这个技能完成以下任务：'))).slice(0, 100000);
          $('settings-dialog').close(); resizePrompt(); $('prompt').focus(); updateRunState();
        };
        actions.append(use);
      }
      card.append(actions); container.append(card);
    }
  }
}
async function copyText(text) { try { if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text); else { const field = document.createElement('textarea'); field.value = text; document.body.append(field); field.select(); if (!document.execCommand('copy')) throw new Error(); field.remove(); } toast(t('已复制')); } catch { toast(t('复制失败，请选择文字手动复制')); } }

function resizePrompt() {
  const prompt = $('prompt');
  if (!prompt.value) { prompt.style.height = ''; return; }
  prompt.style.height = '0px';
  const maximum = parseFloat(getComputedStyle(prompt).maxHeight) || 180;
  prompt.style.height = Math.min(maximum, prompt.scrollHeight) + 'px';
}

async function restoreWorkspace() {
  $('startup-screen').hidden = false; $('startup-retry').hidden = true;
  $('startup-message').textContent = t('正在恢复你的对话…');
  try {
    const saved = savedThread();
    let data;
    try { data = await api('/bootstrap' + (saved ? '?thread=' + encodeURIComponent(saved) : '')); }
    catch (error) {
      // Keep the updated frontend usable while a running server waits to restart.
      if (error.status !== 404) throw error;
      const status = await api('/status');
      if (status.setupRequired) data = {...status, authenticated: false};
      else { try { data = {...await api('/me'), authenticated: true}; } catch (error) { if (error.status !== 401) throw error; data = {...status, authenticated: false}; } }
    }
    if (data.authenticated) await enterWorkspace(data);
    else { showAuth(data.setupRequired); if (!data.setupRequired) setLoginLock(data); }
  } catch (error) {
    if (state.csrf) { $('startup-screen').hidden = true; toast(t('对话暂未恢复：') + error.message); }
    else { $('startup-message').textContent = t('暂时无法连接服务器：') + error.message; $('startup-retry').hidden = false; }
  }
}

function initializeApp() {
  captureStaticTranslations();
  applyStaticLanguage();
  setInterval(updateLoginLock, 1000);
  setInterval(refreshLoginLock, 15000);
  setInterval(() => { if (!$('workspace').hidden && ['running','waiting'].includes(state.thread?.status)) updateClocks(); }, 250);
  $('auth-form').onsubmit = async event => {
    event.preventDefault(); if (authPending || (!state.setup && authLockedUntil > Date.now())) return; $('auth-error').textContent = '';
    if (state.setup && $('auth-password').value !== $('auth-confirm').value) { $('auth-error').textContent = t('两次输入的密码不一致'); return; }
    authPending = true; $('auth-submit').disabled = true;
    try { const data = await api(state.setup ? '/setup' : '/login', {username:$('auth-username').value.trim(),password:$('auth-password').value}); authLockedUntil = 0; lockWasActive = false; $('auth-form').reset(); await enterWorkspace(data); }
    catch (e) { $('auth-error').textContent = e.message; $('auth-password').value = ''; if (e.details?.retryAfter) setLoginLock(e.details); }
    finally { authPending = false; $('auth-submit').disabled = false; updateLoginLock(); }
  };
  $('password-toggle').onclick = () => { const show = $('auth-password').type === 'password'; $('auth-password').type = show ? 'text' : 'password'; $('password-toggle').setAttribute('aria-label',show ? t('隐藏密码') : t('显示密码')); };
  $('new-chat').onclick = newChat;
  $('search').oninput = renderThreadList;
  $('composer-form').onsubmit = sendMessage;
  $('prompt').oninput = () => { resizePrompt(); updateRunState(); };
  window.addEventListener('resize', resizePrompt);
  $('attach-image').onclick = () => $('image-input').click();
  $('image-input').onchange = () => { addImageFiles([...$('image-input').files]); $('image-input').value = ''; };
  $('prompt').addEventListener('paste', event => { const files = [...(event.clipboardData?.files || [])]; if (files.length) { event.preventDefault(); addImageFiles(files); } });
  $('workspace').addEventListener('dragenter', event => { if (event.dataTransfer?.types.includes('Files')) { event.preventDefault(); imageDragDepth++; $('composer-form').classList.add('drag-over'); } });
  $('workspace').addEventListener('dragover', event => { if (event.dataTransfer?.types.includes('Files')) { event.preventDefault(); event.dataTransfer.dropEffect = 'copy'; } });
  $('workspace').addEventListener('dragleave', event => { if (event.dataTransfer?.types.includes('Files')) { imageDragDepth = Math.max(0, imageDragDepth - 1); if (!imageDragDepth) $('composer-form').classList.remove('drag-over'); } });
  $('workspace').addEventListener('drop', event => { if (event.dataTransfer?.files.length) { event.preventDefault(); imageDragDepth = 0; $('composer-form').classList.remove('drag-over'); addImageFiles([...event.dataTransfer.files]); } });
  $('close-image').onclick = () => $('image-dialog').close();
  $('image-dialog').addEventListener('close', () => { $('image-viewer-image').removeAttribute('src'); });
  $('close-file').onclick = () => $('file-dialog').close();
  $('file-dialog').addEventListener('close', () => { filePreviewRequest++; });
  $('scroll-area').addEventListener('scroll', () => { const scroll = $('scroll-area'); pinToBottom = scroll.scrollHeight - scroll.scrollTop - scroll.clientHeight < 100; }, {passive: true});
  $('prompt').onkeydown = event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); $('composer-form').requestSubmit(); } };
  $('stop-button').onclick = async () => { if (!state.thread) return; $('stop-button').disabled = true; try { await api('/threads/'+state.thread.id+'/interrupt',{}); toast(t('已请求停止任务')); } catch (e) { toast(e.message); } finally { updateRunState(); } };
  for (const button of document.querySelectorAll('[data-prompt]')) button.onclick = () => { $('prompt').value = button.dataset.prompt; resizePrompt(); $('prompt').focus(); updateRunState(); };
  $('sidebar-open').onclick = () => { $('sidebar').classList.add('open'); $('sidebar-backdrop').hidden = false; };
  $('sidebar-close').onclick = closeSidebar;
  $('sidebar-backdrop').onclick = closeSidebar;
  $('open-settings').onclick = () => openSettings();
  $('open-extensions').onclick = () => openSettings('extensions');
  $('refresh-extensions').onclick = () => loadExtensions(true);
  $('project-button').onclick = openProjectDialog;
  $('close-settings').onclick = () => $('settings-dialog').close();
  $('add-project').onclick = openProjectDialog;
  $('close-project').onclick = () => $('project-dialog').close();
  $('cancel-project').onclick = () => $('project-dialog').close();
  $('browse-folder').onclick = () => browseDirectories($('project-path').value.trim());
  $('folder-up').onclick = () => { if (folderParent) browseDirectories(folderParent); };
  $('project-dialog').addEventListener('close', () => { folderBrowseRequest++; });
  $('project-form').onsubmit = async event => {
    event.preventDefault(); const button = $('save-project'); button.disabled = true; $('project-error').textContent = '';
    const selection = state.selection;
    try {
      const result = await api('/projects', {path: $('project-path').value.trim()});
      state.projects = result.projects; state.settings = result.settings; collapsedProjects.delete(result.project.id);
      $('project-dialog').close();
      if (selection === state.selection) { newChat({preserveDraft: true}); updateRunState(); } else { applySettings(); renderThreadList(); }
      toast(t('项目文件夹已保存，下次登录可直接使用'));
    } catch (error) { $('project-error').textContent = error.message; }
    finally { button.disabled = false; }
  };
  for (const button of document.querySelectorAll('[data-tab]')) button.onclick = () => selectSettingsTab(button.dataset.tab);
  $('general-form').onsubmit = async event => {
    event.preventDefault(); const button = $('general-form').querySelector('[type=submit]'); button.disabled = true; $('general-error').textContent = '';
    try { state.settings = await api('/settings',{cwd:$('setting-cwd').value.trim(),model:$('setting-model').value.trim(),effort:$('setting-effort').value,sandbox:$('setting-sandbox').value,approvalPolicy:$('setting-approval').value,theme:$('setting-theme').value}); applySettings(); await refreshProjects(); toast(t('工作偏好已保存')); $('settings-dialog').close(); }
    catch (e) { $('general-error').textContent = e.message; } finally { button.disabled = false; }
  };
  $('credentials-form').onsubmit = async event => {
    event.preventDefault(); $('credentials-error').textContent = '';
    if ($('new-password').value !== $('confirm-password').value) { $('credentials-error').textContent = t('两次输入的密码不一致'); return; }
    const button = $('credentials-form').querySelector('[type=submit]'); button.disabled = true;
    try { const data = await api('/credentials',{currentPassword:$('current-password').value,username:$('setting-username').value.trim(),password:$('new-password').value}); state.csrf = data.csrf; state.username = data.username; $('account-name').textContent = data.username; $('avatar').textContent = data.username.slice(0,1).toUpperCase(); $('credentials-form').reset(); $('settings-dialog').close(); connectEvents(); toast(t('账号与密码已更新，其他登录已失效')); }
    catch (e) { $('credentials-error').textContent = e.message; } finally { button.disabled = false; }
  };
  $('logout').onclick = async () => { try { await api('/logout',{}); rememberThread(null); showAuth(false); } catch (e) { toast(e.message); } };
  $('model-picker').onchange = async () => { const model = $('model-picker').value; try { state.settings = await api('/settings',{model}); applySettings(); toast(t('模型已更新，将在下次发送时使用')); } catch (e) { toast(e.message); applySettings(); } };
  $('effort-picker').onchange = async () => { try { state.settings = await api('/settings',{effort:$('effort-picker').value}); applySettings(); } catch (e) { toast(e.message); applySettings(); } };
  $('show-changes').onclick = () => { $('changes-panel').hidden = !$('changes-panel').hidden; if (!$('changes-panel').hidden) { changesDirty = true; renderChanges(); } };
  $('close-changes').onclick = () => $('changes-panel').hidden = true;
  $('close-text').onclick = () => $('text-dialog').close();
  $('changes-body').onclick = async event => { const button = event.target.closest('.preview-file'); if (!button || !state.thread) return; try { const data = await api('/files?thread='+encodeURIComponent(state.thread.id)+'&path='+encodeURIComponent(button.dataset.path)); $('text-dialog-title').textContent = data.path; $('text-dialog-body').textContent = data.text; $('text-dialog').showModal(); } catch (e) { toast(e.message); } };
  $('messages').onclick = event => { const button = event.target.closest('.copy-button'); if (button) copyText(button.closest('pre').querySelector('code').textContent); const image = event.target.closest('.message-image'); if (image && safeImageURL(image.dataset.imageUrl)) { $('image-viewer-image').src = image.dataset.imageUrl; $('image-dialog-title').textContent = image.dataset.imageName || t('图片预览'); $('image-dialog').showModal(); } };
  $('messages').addEventListener('toggle', event => {
    const node = event.target;
    if (!node.matches('details[data-item-id]') || !node.open) return;
    const item = state.items.find(item => item.id === node.dataset.itemId);
    if (item) { renderToolBody(node, item); updateClocks(); }
  }, true);
  $('messages').addEventListener('click', event => { const button = event.target.closest('[data-file-id]'); if (button) previewFile(button.dataset.fileId); });
  $('thread-menu').onclick = () => {
    const old = document.querySelector('.thread-menu-popover'); if (old) { old.remove(); return; }
    if (!state.thread) { toast(t('开始一段对话后，可以重命名或归档')); return; }
    const menu = document.createElement('div'); menu.className = 'thread-menu-popover';
    for (const [label,action] of [[t('重命名对话'),'rename'],[t('归档对话'),'archive']]) { const button = document.createElement('button'); button.textContent = label; button.onclick = async () => { menu.remove(); const tid = state.thread?.id; if (!tid) return; try { if (action === 'rename') { const title = window.prompt(t('输入对话名称'),state.thread.title); if (!title?.trim()) return; await api('/threads/'+tid+'/rename',{title}); } else { await api('/threads/'+tid+'/archive',{}); newChat(); toast(t('对话已归档')); } await refreshThreads(); } catch (e) { toast(e.message); } }; menu.append(button); }
    document.body.append(menu);
  };
  document.addEventListener('click', event => { if (!event.target.closest('.thread-menu-popover') && !event.target.closest('#thread-menu')) document.querySelector('.thread-menu-popover')?.remove(); if (!event.target.closest('.project-menu-popover') && !event.target.closest('.project-more')) document.querySelector('.project-menu-popover')?.remove(); });
  document.addEventListener('keydown', event => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k' && state.csrf && !$('settings-dialog').open) { event.preventDefault(); newChat(); } });
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change',applyTheme);
  window.addEventListener('online', () => { if (state.csrf) connectEvents(); });
  $('startup-retry').onclick = restoreWorkspace;
  restoreWorkspace();
  for (const picker of document.querySelectorAll("[data-language-picker]")) picker.onchange = () => setUILanguage(picker.value);
}
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initializeApp, {once: true});
else initializeApp();
