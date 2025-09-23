# How to View Mermaid Diagrams on GitHub

## Automatic Rendering on GitHub

Once you push a `.md` file containing Mermaid diagrams to GitHub, they will automatically render:

1. **Navigate to your repository** on GitHub
2. **Click on the file**: `docs/system-design-diagram.md`
3. **The diagram renders automatically** - GitHub has native Mermaid support since 2022

## What You'll See

- The Mermaid code block will be replaced with an interactive diagram
- You can zoom, pan, and click on elements
- The diagram will have proper styling and colors as defined in the code

## Alternative Viewing Methods

### Mermaid Live Editor
- **URL**: https://mermaid.live/
- **Use for**: Editing, sharing, or testing Mermaid syntax
- **Features**: Interactive editing, export options, shareable links

### VS Code Preview
- **Extension**: "Mermaid Preview"
- **Usage**: 
  1. Install the extension
  2. Open the `.md` file
  3. Press `Ctrl+Shift+P` → "Mermaid: Preview"

### GitLab
- GitLab also has built-in Mermaid support
- Same process as GitHub

## Troubleshooting

### Diagram Not Rendering
- **Refresh the page** - Sometimes takes a moment
- **Check syntax** - Ensure proper `mermaid` code block format
- **Verify file extension** - Must be `.md` (Markdown)

### Common Issues
- **Syntax errors** in Mermaid code
- **Missing code block markers** (```mermaid)
- **Browser compatibility** - Use modern browsers

## Pro Tips

### Adding Links to README
```markdown
[View System Design Diagram](https://mermaid.live/edit#pako:your-mermaid-code)
```

### Sharing Diagrams
- Use Mermaid Live Editor for shareable links
- GitHub automatically creates viewable diagrams
- VS Code extension for local development

## Supported Mermaid Features on GitHub

- ✅ Flowcharts
- ✅ Sequence diagrams
- ✅ Gantt charts
- ✅ Class diagrams
- ✅ State diagrams
- ✅ User journey diagrams
- ✅ Git graphs
- ✅ Pie charts
- ✅ Requirements diagrams

GitHub's Mermaid rendering is excellent and displays diagrams with proper styling and interactivity!
