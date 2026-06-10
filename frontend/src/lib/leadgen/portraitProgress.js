/** Стадии прогресса поиска по портрету (один POST, таймер до ответа API). */

export const PORTRAIT_PROGRESS_STEPS = [
	'Загружаем эталон из Checko…',
	'Ищем компании: ЕГРЮЛ, Tavily, Brave…',
	'Сравниваем с критериями портрета…',
	'AI-оценка подходящих кандидатов…',
];

/** @param {(label: string) => void} setStep @param {(sec: number) => void} setElapsed */
export function startPortraitProgress(setStep, setElapsed, stepMs = 12_000) {
	let step = 0;
	let sec = 0;
	setStep(PORTRAIT_PROGRESS_STEPS[0]);
	setElapsed(0);
	const stepTimer = setInterval(() => {
		step = Math.min(step + 1, PORTRAIT_PROGRESS_STEPS.length - 1);
		setStep(PORTRAIT_PROGRESS_STEPS[step]);
	}, stepMs);
	const secTimer = setInterval(() => {
		sec += 1;
		setElapsed(sec);
	}, 1000);
	return () => {
		clearInterval(stepTimer);
		clearInterval(secTimer);
	};
}

/** Ширина полосы прогресса (0–95%) по секундам ожидания. */
export function portraitProgressPercent(elapsedSec) {
	return Math.min(95, 15 + elapsedSec * 2);
}
