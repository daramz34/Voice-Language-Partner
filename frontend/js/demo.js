/* Simulated live session replay for the hero.
   Real conversations per language, typed out, waveform on agent lines,
   scorecard fades in at the end, then loops. */

const SCRIPTS = {
  es: {
    convo: [
      { who: "agent", name: "Camarero", text: "¡Buenas tardes! Bienvenidos a La Tasca. ¿Mesa para cuántos?" },
      { who: "user",  name: "Tú",       text: "Una mesa para dos, por favor." },
      { who: "agent", name: "Camarero", text: "Por supuesto. ¿Quieren beber algo mientras deciden?" },
      { who: "user",  name: "Tú",       text: "Sí, dos aguas con hielo." },
    ],
    scores: { grammar: 88, vocabulary: 82, fluency: 74 },
    overall: 81,
    tip: "Recommendation: practice ordering follow-up questions in Spanish.",
  },
  fr: {
    convo: [
      { who: "agent", name: "Serveur", text: "Bonjour ! Bienvenue au Petit Bistrot. Une table pour combien de personnes ?" },
      { who: "user",  name: "Vous",    text: "Une table pour deux, s'il vous plaît." },
      { who: "agent", name: "Serveur", text: "Très bien. Souhaitez-vous quelque chose à boire ?" },
      { who: "user",  name: "Vous",    text: "Oui, deux cafés, s'il vous plaît." },
    ],
    scores: { grammar: 76, vocabulary: 80, fluency: 68 },
    overall: 75,
    tip: "Recommendation: practice polite requests with the conditional.",
  },
  de: {
    convo: [
      { who: "agent", name: "Kellner", text: "Guten Tag! Willkommen im Gasthaus Adler. Für wie viele Personen?" },
      { who: "user",  name: "Du",      text: "Einen Tisch für zwei, bitte." },
      { who: "agent", name: "Kellner", text: "Gerne. Möchten Sie etwas trinken?" },
      { who: "user",  name: "Du",      text: "Zwei Wasser, bitte." },
    ],
    scores: { grammar: 71, vocabulary: 74, fluency: 66 },
    overall: 70,
    tip: "Recommendation: practice the formal 'Sie' forms in restaurant settings.",
  },
};

const body = document.getElementById("demo-body");
let currentLang = "es";
let runId = 0;

function waveform() {
  const w = document.createElement("span");
  w.className = "speaking";
  w.innerHTML = "<i></i><i></i><i></i>";
  return w;
}

function bubble(msg) {
  const b = document.createElement("div");
  b.className = "bubble " + msg.who;
  b.innerHTML = `<span class="tag">${msg.name}</span>`;
  const text = document.createElement("span");
  b.appendChild(text);
  if (msg.who === "agent") b.appendChild(waveform());
  body.appendChild(b);
  // typewriter
  let i = 0;
  const tick = () => {
    if (runMarker !== runId) return;
    text.textContent = msg.text.slice(0, ++i);
    if (i < msg.text.length) setTimeout(tick, 22);
    else b.querySelector(".speaking")?.remove();
  };
  tick();
  return b;
}

function scorecard(data, mount) {
  const card = document.createElement("div");
  card.className = "scorecard";
  card.innerHTML = `
    <div class="scorecard-head"><strong>Session report</strong><span class="score-big">${data.overall}</span></div>
    ${Object.entries(data.scores).map(([k, v]) => `
      <div class="score-row"><span>${k}</span><div class="bar"><i data-w="${v}"></i></div><b>${v}</b></div>
    `).join("")}
    <div class="score-tip">${data.tip}</div>`;
  mount.appendChild(card);
  requestAnimationFrame(() => {
    card.classList.add("show");
    card.querySelectorAll(".bar i").forEach(b => (b.style.width = b.dataset.w + "%"));
  });
  return card;
}

let runMarker = 0;

async function play(lang) {
  runMarker = ++runId;
  body.innerHTML = "";
  const data = SCRIPTS[lang];

  for (const msg of data.convo) {
    if (runMarker !== runId) return;
    bubble(msg);
    await new Promise(r => setTimeout(r, 1900));
  }
  if (runMarker !== runId) return;

  await new Promise(r => setTimeout(r, 500));
  const card = scorecard(data, body);
  await new Promise(r => setTimeout(r, 5200));
  if (runMarker === runId) play(lang); // loop
}

document.querySelectorAll(".lang-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".lang-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
    play(tab.dataset.lang);
  });
});

// static report card in the "Your report" section
scorecard(
  { scores: { grammar: 91, vocabulary: 85, fluency: 78 }, overall: 85,
    tip: "You struggled with past tense verbs. Practice them in tutor mode." },
  document.getElementById("static-report")
);

play(currentLang);
