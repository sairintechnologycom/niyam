const tl = require('azure-pipelines-task-lib/task');
const cp = require('child_process');

async function run() {
    try {
        const targetBranch = tl.getInput('targetBranch', true);
        const strict = tl.getBoolInput('strict', false);
        const minScore = tl.getInput('minScore', false) || "50";
        const publicKey = tl.getInput('publicKey', false);
        const version = tl.getInput('version', false) || "latest";

        console.log(`Setting up Niyam (version: ${version})...`);
        
        // Ensure pip is available and install niyam
        const installCmd = version === "latest" ? "pip install niyam" : `pip install niyam==${version}`;
        try {
            cp.execSync(installCmd, { stdio: 'inherit' });
        } catch (err) {
            tl.setResult(tl.TaskResult.Failed, `Failed to install Niyam: ${err.message}`);
            return;
        }

        console.log(`Running Niyam CI Verify for branch: ${targetBranch}`);
        
        const args = ['ci', 'verify', '--target', targetBranch, '--min-score', minScore];
        if (strict) {
            args.push('--strict');
        }

        // Set public key in environment if provided
        const env = { ...process.env };
        if (publicKey) {
            env['NIYAM_PUBLIC_KEY'] = publicKey;
            console.log("Using provided public key for zero-trust verification.");
        }

        const niyamProcess = cp.spawnSync('niyam', args, { 
            stdio: 'inherit',
            env: env,
            shell: true
        });

        if (niyamProcess.status !== 0) {
            tl.setResult(tl.TaskResult.Failed, `Niyam verification failed with exit code ${niyamProcess.status}`);
        } else {
            tl.setResult(tl.TaskResult.Succeeded, "Niyam verification passed.");
        }

    } catch (err) {
        tl.setResult(tl.TaskResult.Failed, err.message);
    }
}

run();
