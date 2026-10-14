## Description:

VMake helps agents process image or video watermark removal and quality restoration through the Vmake AI service while discovering available tasks from the remote catalog before execution.

This skill is ready for commercial/non-commercial use.

## Publisher:

[wemayiiii](https://clawhub.ai/user/wemayiiii)

### License/Terms of Use:

MIT-0

## Use Case:

External users and developers use this skill to route image or video assets through Vmake AI for watermark removal, quality restoration, enhancement, or upscaling. It is designed for agent-mediated workflows that need credential checks, task discovery, quota-aware execution, polling, and result delivery.

### Deployment Geography for Use:

Global

## Known Risks and Mitigations:

Risk: The skill processes user media through an external Vmake service and configured messaging platforms.

Mitigation: Install only when those services are trusted with the media, require explicit user authorization before upload and quota use, and use scoped credentials.

Risk: The security summary notes arbitrary server messages and links may be relayed to users.

Mitigation: Review server-provided notices and action links before acting on them or presenting them as authoritative next steps.

Risk: The security guidance identifies under-scoped network and download paths for user media and service endpoints.

Mitigation: Run in a network-restricted environment, avoid untrusted media URLs, and prefer direct uploads or resolved local files when URL reliability is uncertain.

Risk: Dependencies and runtime scripts may change behavior if installed without pinning.

Mitigation: Pin dependencies and review the artifact and scan results before production deployment.

## Reference(s):

- [VMake skill page](https://clawhub.ai/wemayiiii/skills/vmake-skill)
- [Vmake Developers API Key](https://vmake.ai/developers#api-key)
- [README](README.md)
- [Errors, polling, and environment tuning](docs/errors-and-polling.md)
- [IM attachments and resolve-input](docs/im-attachments.md)
- [Multi-platform delivery](docs/multi-platform.md)
- [Feishu video delivery](docs/feishu-send-video.md)

## Skill Output:

**Output Type(s):** [text, markdown, shell commands, configuration, guidance]

**Output Format:** [Markdown guidance with inline shell commands and JSON command output]

**Output Parameters:** [1D]

**Other Properties Related to Output:** [May return URLs or local file paths for processed media results; long-running video work uses asynchronous worker guidance.]

## Skill Version(s):

2.0.0 (source: server release evidence and artifact skill.json)

## Ethical Considerations:

Users should evaluate whether this skill is appropriate for their environment, review any generated or modified files before relying on them, and apply their organization's safety, security, and compliance requirements before deployment.
