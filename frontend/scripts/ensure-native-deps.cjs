/**
 * npm/cli#4828 + win32: npm (x64) vs node (arm64) — дотягиваем native bindings.
 */
const { execSync } = require('node:child_process');
const { existsSync } = require('node:fs');
const { join } = require('node:path');

const root = join(__dirname, '..');

function hasPkg(name) {
	return existsSync(join(root, 'node_modules', name));
}

function npmInstall(pkg) {
	execSync(`npm install ${pkg} --no-save --force --os=win32 --cpu=arm64`, {
		cwd: root,
		stdio: 'inherit',
		env: { ...process.env, npm_config_arch: 'arm64', npm_config_platform: 'win32' },
	});
}

if (process.platform !== 'win32') process.exit(0);

const needLightning = !existsSync(
	join(root, 'node_modules', 'lightningcss', 'lightningcss.win32-arm64-msvc.node'),
);
if (needLightning && !hasPkg('lightningcss-win32-arm64-msvc')) {
	try {
		npmInstall('lightningcss-win32-arm64-msvc@1.32.0');
	} catch (e) {
		console.warn('[ensure-native-deps] lightningcss binding:', e.message);
	}
}
