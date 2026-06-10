import { PORTRAIT_PROGRESS_STEPS, portraitProgressPercent } from './portraitProgress.js';

if (PORTRAIT_PROGRESS_STEPS.length < 3) process.exit(1);
if (portraitProgressPercent(0) !== 15) process.exit(2);
if (portraitProgressPercent(100) !== 95) process.exit(3);
console.log('portraitProgress.smoke: ok');
