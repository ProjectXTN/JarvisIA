import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
	console.log('Jarvis Copilot is now active!');

	const interval = setInterval(() => {
		const code = vscode.window.activeTextEditor?.document.getText();
		if (code) {
			fetch("http://localhost:11600/suggest", {
				method: "POST",
				body: JSON.stringify({ code }),
				headers: { "Content-Type": "application/json" }
			})
				.then((res) => res.json() as Promise<{ suggestion: string }>)
				.then(({ suggestion }) => {
					vscode.window.showInformationMessage(`Jarvis diz: ${suggestion}`);
				});
		}
	}, 3000);
}

export function deactivate() { }
