请帮助我将当前项目代码安全地上传到 GitHub。请严格按以下步骤执行，遇到任何敏感信息或异常立即中断并提示我：

1. **检查/生成 .gitignore**  
   - 如果项目根目录没有 `.gitignore`，请根据当前项目的主要语言（自动检测，如 Python、JavaScript、Java 等）生成一个标准模板，必须包含：`__pycache__/`、`*.pyc`、`.env`、`.env.*`、`*.log`、`node_modules/`、`*.secret`、`*.key`、`*.pem`、`*.p12`、`.DS_Store`、`dist/`、`build/`、`*.tmp`。  
   - 如果已有 `.gitignore`，请检查是否包含以上常见条目，缺少的请询问我是否补充。

2. **强制敏感信息扫描（使用专业工具）**  
   - 首先检测系统中是否已安装 `git-secrets` 或 `trufflehog`。  
     - 如果已安装 `git-secrets`，请执行 `git secrets --scan`，若扫描出任何可能的密钥，列出具体文件和行号，并立即中止推送流程，等待我手动处理。  
     - 如果已安装 `trufflehog`，请执行 `trufflehog filesystem . --only-verified --fail`，若有发现也中止并提示。  
     - 如果两者都未安装，请提示我“**未安装敏感信息扫描工具，是否改用内置的正则检查？**”，若我同意，则执行步骤 2.1 的内置正则扫描。  
   - **内置正则检查（备用方案）**：使用 `git diff --cached` 或 `git grep -n -E "API_KEY|SECRET|PASSWORD|TOKEN|PRIVATE_KEY"` 扫描暂存区，发现匹配项则列出并中止。

3. **初始化与暂存**  
   - 若未初始化 Git 仓库，执行 `git init`。  
   - 执行 `git add .`（严格遵循 .gitignore，排除被忽略的文件）。

4. **二次确认安全提示**  
   - 在执行 `git commit` 之前，输出一条醒目的警告：“⚠️ 即将提交以下文件列表（展示 `git status --short`），请人工确认没有包含 `.env`、密钥文件或本地配置。如果确认安全，请输入 `yes` 继续，否则输入 `no` 中止。”  
   - 等待我的回复，只有收到 `yes` 才继续。

5. **生成规范的提交信息**  
   - 根据暂存的更改内容，自动生成符合 Conventional Commits 规范的提交信息（例如 `feat: 添加用户认证模块`），并执行 `git commit -m "..."`。

6. **关联与推送**  
   - 检查是否已关联远程仓库 `origin`，若未关联，请提示我输入 GitHub 仓库地址（格式：`https://github.com/用户名/仓库名.git` 或 `git@github.com:用户名/仓库名.git`），并执行 `git remote add origin <url>`。  
   - 推送到远程仓库的 `main` 分支：`git push -u origin main`。如果推送失败（比如远程有新的提交），提示我先执行 `git pull --rebase` 并解决冲突。

**重要原则**：  
- 一旦扫描到任何可疑敏感信息，必须立即中止整个流程，绝不自动提交或推送。  
- 每一步的输出要清晰易懂，方便我判断。