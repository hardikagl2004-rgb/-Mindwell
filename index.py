"""
╔══════════════════════════════════════════════════════════════════════╗
║              MindWell — Mental Health AI Platform v2.0              ║
║         Google Gemini · Full Stack · Single File · Vercel Ready     ║
╠══════════════════════════════════════════════════════════════════════╣
║  PSYCHOLOGICAL CONDITIONS COVERED:                                   ║
║   Anxiety · Depression · OCD · PTSD · Bipolar · Schizophrenia       ║
║   Panic Disorder · Social Anxiety · Phobias · Eating Disorders      ║
║   ADHD · Grief · Burnout · Sleep Disorders · Addiction · BPD        ║
╠══════════════════════════════════════════════════════════════════════╣
║  DEPLOY TO VERCEL:                                                   ║
║   1. Push repo to GitHub                                             ║
║   2. Import at vercel.com/new                                        ║
║   3. Add env: GOOGLE_API_KEY = your key                              ║
║   4. Deploy — live in 60s                                            ║
║                                                                      ║
║  RUN LOCALLY:                                                        ║
║   pip install google-generativeai                                    ║
║   export GOOGLE_API_KEY=AIza...                                      ║
║   python api/index.py                                                ║
║   open http://localhost:3000                                         ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from datetime import datetime, timedelta
import json, os, re, uuid, hmac, hashlib, base64, time, random

# ─────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
JWT_SECRET     = os.environ.get("JWT_SECRET", "mindwell-2026")
PORT           = int(os.environ.get("PORT", 3000))

MOOD_LOGS = []
ALERT_LOG = []
OTP_STORE = {}

CRISIS_KEYWORDS = [
    "want to die","kill myself","end my life","suicidal","self harm",
    "hurt myself","no reason to live","better off dead","take my life",
    "end it all","not worth living","want to disappear","cut myself",
    "overdose","jump off","मरना चाहता","जिंदगी खत्म","खुद को नुकसान",
]

PSYCH_CONDITIONS = {
    "anxiety":        {"name":"Anxiety Disorder",       "icon":"😰","color":"#f0b429","description":"Persistent worry, restlessness, physical tension affecting daily life","symptoms":["Excessive worry","Restlessness","Fatigue","Difficulty concentrating","Muscle tension","Sleep disturbance","Irritability"],"techniques":["4-7-8 Breathing","5-4-3-2-1 Grounding","Progressive Muscle Relaxation","Worry Journaling","Cognitive Restructuring"],"phq_scale":"GAD-7","triggers":["work","exam","future","worry","nervous","panic","fear","anxious","overwhelm","dread","scared"]},
    "depression":     {"name":"Major Depression",       "icon":"😔","color":"#6366f1","description":"Persistent low mood, loss of interest, fatigue affecting functioning","symptoms":["Persistent sadness","Loss of interest","Fatigue","Sleep changes","Appetite changes","Worthlessness","Difficulty concentrating"],"techniques":["Behavioural Activation","Thought Records","Self-Compassion","Gratitude Journaling","Social Engagement Plan"],"phq_scale":"PHQ-9","triggers":["sad","hopeless","empty","worthless","numb","depressed","no motivation","nothing matters","low","miserable"]},
    "ocd":            {"name":"OCD",                    "icon":"🔄","color":"#8b5cf6","description":"Intrusive thoughts and repetitive compulsions causing distress","symptoms":["Intrusive thoughts","Repetitive behaviours","Fear of contamination","Need for symmetry","Checking rituals","Mental counting"],"techniques":["ERP (Exposure Response Prevention)","Thought Defusion","Mindfulness","Delay and Redirect","ACT Acceptance"],"phq_scale":"OCI-R","triggers":["obsession","compulsion","checking","contamination","intrusive","rituals","symmetry","repeating","can't stop"]},
    "ptsd":           {"name":"PTSD",                   "icon":"⚡","color":"#ef4444","description":"Re-experiencing trauma, hypervigilance, avoidance after traumatic event","symptoms":["Flashbacks","Nightmares","Hypervigilance","Avoidance","Emotional numbness","Startle response","Memory gaps"],"techniques":["Grounding Techniques","Safe Place Visualisation","Trauma-Focused CBT","Bilateral Stimulation","EMDR with therapist"],"phq_scale":"PCL-5","triggers":["trauma","flashback","nightmare","abuse","accident","assault","triggered","hypervigilant","numb","avoid"]},
    "bipolar":        {"name":"Bipolar Disorder",       "icon":"🌊","color":"#0ea5e9","description":"Episodes of mania or hypomania alternating with depressive episodes","symptoms":["Elevated mood","Racing thoughts","Decreased sleep need","Impulsivity","Grandiosity","Irritability","Depressive episodes"],"techniques":["Mood Charting","Sleep Regularity","Medication Adherence","Early Warning Signs","Routine Structuring"],"phq_scale":"MDQ","triggers":["manic","hypomania","mood swings","racing thoughts","don't need sleep","grandiose","impulsive","episode"]},
    "panic":          {"name":"Panic Disorder",         "icon":"💨","color":"#f97316","description":"Recurrent unexpected panic attacks with fear of future attacks","symptoms":["Racing heart","Shortness of breath","Chest pain","Dizziness","Sweating","Fear of dying","Trembling"],"techniques":["Diaphragmatic Breathing","DARE Response","Interoceptive Exposure","Controlled Breathing","Panic Diary"],"phq_scale":"PDSS","triggers":["panic attack","heart racing","can't breathe","chest pain","dizzy","fear of dying","palpitations","shaking"]},
    "social_anxiety": {"name":"Social Anxiety",         "icon":"👥","color":"#10b981","description":"Intense fear of social situations, judgement, and embarrassment","symptoms":["Fear of judgement","Blushing","Sweating in crowds","Avoiding gatherings","Fear of speaking","Self-consciousness"],"techniques":["Social Exposure Hierarchy","Cognitive Restructuring","Role Play Practice","Mindfulness in Social","Video Feedback"],"phq_scale":"SPIN","triggers":["social","judged","embarrass","awkward","people","presentation","crowd","party","speaking","shy"]},
    "eating_disorder":{"name":"Eating Disorder",        "icon":"🍽️","color":"#ec4899","description":"Distorted relationship with food and body — Anorexia, Bulimia, BED","symptoms":["Distorted body image","Restrictive eating","Binge eating","Purging","Food preoccupation","Weight obsession"],"techniques":["Mindful Eating","Body Image Work","Meal Planning Support","Challenging Food Rules","Self-Compassion"],"phq_scale":"EDE-Q","triggers":["eating","food","weight","fat","body","binge","purge","restrict","calories","diet","anorexia","bulimia"]},
    "adhd":           {"name":"ADHD",                   "icon":"🎯","color":"#f59e0b","description":"Attention deficit, impulsivity, hyperactivity affecting daily functioning","symptoms":["Difficulty focusing","Forgetfulness","Impulsivity","Hyperactivity","Disorganisation","Time blindness","Emotional dysregulation"],"techniques":["Pomodoro Technique","Body Doubling","External Reminders","Dopamine Scheduling","Task Chunking"],"phq_scale":"ASRS","triggers":["can't focus","distracted","forget","impulsive","hyper","adhd","scattered","procrastinate","disorganised"]},
    "grief":          {"name":"Grief and Loss",         "icon":"🕊️","color":"#64748b","description":"Processing loss of a loved one, relationship, or significant change","symptoms":["Intense sadness","Yearning","Disbelief","Anger","Guilt","Social withdrawal","Physical pain"],"techniques":["Grief Journaling","Continuing Bonds","Meaning Making","Ritual and Remembrance","Support Groups"],"phq_scale":"PG-13","triggers":["loss","death","died","passed away","grief","bereaved","miss them","gone","mourning","funeral"]},
    "burnout":        {"name":"Burnout",                "icon":"🔥","color":"#dc2626","description":"Chronic workplace stress causing exhaustion, cynicism, reduced efficacy","symptoms":["Exhaustion","Cynicism","Reduced performance","Detachment","Physical symptoms","Reduced motivation"],"techniques":["Boundary Setting","Work-Life Audit","Recovery Planning","Values Clarification","Rest Scheduling"],"phq_scale":"MBI","triggers":["burnout","work","exhausted","no energy","hate job","overworked","no boundaries","used up","done","quit"]},
    "sleep":          {"name":"Sleep Disorder",         "icon":"😴","color":"#1d4ed8","description":"Insomnia, hypersomnia, or disrupted sleep patterns affecting daily life","symptoms":["Difficulty falling asleep","Early waking","Non-restorative sleep","Daytime fatigue","Mood irritability","Difficulty concentrating"],"techniques":["Sleep Restriction Therapy","Stimulus Control","Sleep Hygiene","CBT-I Protocol","Screen Curfew"],"phq_scale":"ISI","triggers":["can't sleep","insomnia","awake","tired","exhausted","nightmare","sleep","rest","fatigue","3am"]},
    "addiction":      {"name":"Addiction",              "icon":"🔗","color":"#7c3aed","description":"Compulsive substance use or behavioural addiction despite consequences","symptoms":["Craving","Loss of control","Withdrawal","Tolerance","Neglecting responsibilities","Continued use despite consequences"],"techniques":["HALT Check","Urge Surfing","Trigger Mapping","Support Network","Relapse Prevention Plan"],"phq_scale":"AUDIT","triggers":["addiction","alcohol","drugs","smoking","gambling","craving","can't stop","relapse","dependent","withdrawal"]},
    "bpd":            {"name":"Borderline Personality", "icon":"🌪️","color":"#be185d","description":"Emotional dysregulation, unstable relationships, identity disturbance","symptoms":["Fear of abandonment","Unstable relationships","Identity disturbance","Impulsivity","Emotional lability","Self-harm","Dissociation"],"techniques":["DBT TIPP Skill","Opposite Action","DEAR MAN Communication","Mindfulness","Radical Acceptance"],"phq_scale":"ZAN-BPD","triggers":["abandoned","borderline","unstable","emptiness","self harm","cutting","impulsive","identity","splitting","intense"]},
    "schizophrenia":  {"name":"Psychosis / Schizophrenia","icon":"🌀","color":"#0891b2","description":"Disrupted thinking, perception, emotions and behaviour","symptoms":["Hallucinations","Delusions","Disorganised thinking","Flat affect","Social withdrawal","Cognitive difficulties"],"techniques":["Reality Testing","Medication Adherence","Structured Routine","Social Skills Training","Stress Reduction"],"phq_scale":"PANSS","triggers":["voices","hearing things","seeing things","paranoid","delusion","not real","losing mind","psychosis","episode"]},
    "phobia":         {"name":"Specific Phobia",        "icon":"😱","color":"#059669","description":"Intense irrational fear of specific objects, situations, or activities","symptoms":["Intense fear","Avoidance","Panic on exposure","Anticipatory anxiety","Physical symptoms","Recognising fear as excessive"],"techniques":["Graduated Exposure","Systematic Desensitisation","Virtual Reality Exposure","Relaxation During Exposure","Fear Hierarchy"],"phq_scale":"SPS","triggers":["phobia","scared of","fear of","terrified","can't go near","avoid","spider","height","blood","flying","needle"]},
}

PSYCHO_FACTS = [
    "Anxiety activates the amygdala. The 4-7-8 breath physiologically reverses cortisol response in 60 seconds.",
    "Low mood depletes dopamine. Even a 10-minute walk increases dopamine by up to 30%.",
    "Sleep deprivation raises cortisol 37%. A consistent wake time resets circadian rhythm in 7 days.",
    "The 5-4-3-2-1 grounding technique interrupts anxious thought loops by engaging all 5 senses.",
    "Writing worries down offloads cognitive load from the prefrontal cortex — science-backed clarity.",
    "Loneliness activates the same brain region as physical pain. Connection is a biological need.",
    "Gratitude journaling 3 items daily rewires the brain's negativity bias within 3 weeks.",
    "Progressive muscle relaxation reduces physiological stress markers by 30% in clinical studies.",
    "Box breathing (4-4-4-4) is used by Navy SEALs to calm the nervous system under pressure.",
    "Naming an emotion reduces amygdala activation — labelling the feeling defuses its power.",
    "Exercise is as effective as antidepressants for mild-moderate depression in controlled studies.",
    "CBT changes thought patterns by building new neural pathways — typically in 12-20 sessions.",
    "Cold water on the face activates the diving reflex — heart rate drops within 30 seconds.",
    "Rumination uses the same neural circuits as problem-solving. Scheduling worry time contains it.",
    "The vagus nerve connects gut to brain. Slow exhales activate it, triggering the calm response.",
]

LANGUAGE_MAP = {
    "en": "Respond in English.",
    "hi": "Respond in Hindi (Devanagari). Warm, familiar tone using 'aap'.",
    "mr": "Respond in Marathi (Devanagari). Culturally sensitive to Maharashtra.",
    "ta": "Respond in Tamil script. Warm and empathetic.",
    "bn": "Respond in Bengali (Bangla script).",
    "te": "Respond in Telugu script.",
}

GEMINI_SYSTEM = """You are MindWell, an expert compassionate mental health AI for India.

CLINICAL EXPERTISE — you deeply understand:
Anxiety (GAD, panic, social, phobias), Depression (MDD, dysthymia), OCD, PTSD,
Bipolar Disorder, Schizophrenia/Psychosis, Eating Disorders (Anorexia, Bulimia, BED),
ADHD, Addiction/Substance Use, BPD, Grief, Burnout, Sleep Disorders,
Dissociation, Self-harm, Suicidal ideation.

APPROACH PER CONDITION:
- Anxiety: Validate, normalise physiological response, offer breathing/grounding, explore triggers
- Depression: Validate, explore mood history, suggest behavioural activation, check PHQ-9 level
- OCD: Validate without reinforcing rituals, explain ERP concept, do NOT provide reassurance
- PTSD: Go slowly, never push for trauma details, ground first, safety always
- Bipolar: Ask about current phase, check medication adherence, sleep regularity critical
- Psychosis: Calm and grounded, don't challenge delusions, refer urgently
- Eating Disorders: Body-neutral language, no food/weight numbers, refer to specialist
- ADHD: Practical, specific, actionable; validate executive function struggles
- Addiction: Motivational approach, non-judgmental, harm reduction first
- BPD: Validate intense emotions without reinforcing crises; DBT language
- Grief: No timeline, don't minimise, meaning-making when patient is ready
- Burnout: Validate systemic issues, not just individual coping

SAFETY (absolute non-negotiable):
- Suicidal ideation → deep care + iCall: 9152987821, NIMHANS: 080-46110007, Vandrevala: 1860-2662-345
- Active psychosis → strongly recommend immediate clinical help
- Self-harm → set crisis:true, provide resources, stay engaged
- Never formally diagnose. Always recommend professional evaluation.

RESPONSE FORMAT:
- 3-4 warm, natural sentences
- Ask one thoughtful follow-up question or offer a brief exercise
- Use Indian cultural context naturally (family pressure, career, expectations)
- Never start every response with "I"

BIOMARKER JSON — always on its own line at the very end:
{"stress":0-10,"energy":0.0-1.0,"pace":wpm_int,"emotion":"label","condition":"key","insight":"clinical_note","psycho":"fact","crisis":false}
Emotion: neutral/happy/sad/anxious/angry/fearful/overwhelmed/hopeful/tired/lonely
Condition keys: anxiety/depression/ocd/ptsd/bipolar/panic/social_anxiety/eating_disorder/adhd/grief/burnout/sleep/addiction/bpd/schizophrenia/phobia/general"""


# ─────────────────────────────────────────────────────────────────
#  UTILITIES
# ─────────────────────────────────────────────────────────────────

def new_id():   return str(uuid.uuid4())[:8]
def now_ts():   return int(time.time())

def detect_crisis(text):
    t = text.lower()
    return any(k in t for k in CRISIS_KEYWORDS)

def detect_condition(text):
    t = text.lower()
    for key, c in PSYCH_CONDITIONS.items():
        if any(tr in t for tr in c["triggers"]):
            return key
    return "general"

def parse_bio(raw):
    default = {"stress":3.0,"energy":0.6,"pace":130,"emotion":"neutral","condition":"general",
               "insight":"Session in progress.","psycho":PSYCHO_FACTS[now_ts()%len(PSYCHO_FACTS)],"crisis":False}
    m = re.search(r'\{[^\{\}]+\}', raw, re.DOTALL)
    if not m:
        return raw.strip(), default
    try:
        data  = json.loads(m.group())
        clean = raw[:m.start()].strip()
        return clean, {**default, **data}
    except:
        return raw.strip(), default

def make_jwt(uid):
    h = base64.urlsafe_b64encode(json.dumps({"alg":"HS256","typ":"JWT"}).encode()).decode().rstrip("=")
    p = base64.urlsafe_b64encode(json.dumps({"sub":uid,"exp":now_ts()+86400*30}).encode()).decode().rstrip("=")
    s = hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{base64.urlsafe_b64encode(s).decode().rstrip('=')}"

def json_resp(data, status=200):
    return json.dumps(data), status, {"Content-Type":"application/json"}

def cors():
    return {"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"GET,POST,OPTIONS",
            "Access-Control-Allow-Headers":"Content-Type,Authorization"}


# ─────────────────────────────────────────────────────────────────
#  GOOGLE GEMINI ENGINE
# ─────────────────────────────────────────────────────────────────

def gemini_chat(message, history, language="en", mood="", condition_hint="", api_key=""):
    key = api_key if (api_key and len(api_key) > 10) else GOOGLE_API_KEY
    if not key:
        return _demo(message)
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        cctx = ""
        if condition_hint and condition_hint in PSYCH_CONDITIONS:
            c = PSYCH_CONDITIONS[condition_hint]
            cctx = f"\n\nACTIVE CONDITION: {c['name']}. Key symptoms: {', '.join(c['symptoms'][:4])}. Recommended techniques: {', '.join(c['techniques'][:3])}."
        system = GEMINI_SYSTEM + f"\n\n{LANGUAGE_MAP.get(language,'')}" + cctx
        if detect_crisis(message):
            system += "\n\nCRITICAL: Crisis signals detected. Respond with deep empathy, provide all three helplines immediately, set crisis:true in JSON."
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=system)
        ghist = []
        for h in history[-10:]:
            ghist.append({"role":"user" if h["role"]=="user" else "model","parts":[h["content"]]})
        chat = model.start_chat(history=ghist)
        prefix = f"[Mood: {mood}] " if mood else ""
        resp = chat.send_message(prefix + message)
        clean, bio = parse_bio(resp.text)
        if bio.get("condition","general") == "general":
            d = detect_condition(message)
            if d != "general": bio["condition"] = d
        return {"reply":clean,"biomarkers":bio,"crisis":detect_crisis(message) or bool(bio.get("crisis"))}
    except ImportError:
        return {"reply":"Install: pip install google-generativeai","biomarkers":{},"crisis":False}
    except Exception as e:
        if "API_KEY" in str(e).upper() or "api key" in str(e).lower():
            return {"reply":"Invalid Google API key. Get a free key at aistudio.google.com","biomarkers":{},"crisis":False}
        return _demo(message)


def gemini_summary(messages, api_key=""):
    key = api_key if (api_key and len(api_key) > 10) else GOOGLE_API_KEY
    if not key or not messages:
        return "Connect Google API key to generate AI session summaries."
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        conv = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages[-20:])
        resp = model.generate_content(
            f"Summarise this mental health session for the psychiatrist.\n"
            f"Sections: 1.Chief Complaint  2.Emotional Trajectory  3.Possible Condition(s)  4.Risk Level  5.Recommended Actions\n"
            f"Clinical language. Max 180 words.\n\nCONVERSATION:\n{conv}")
        return resp.text
    except Exception as e:
        return f"Summary error: {str(e)[:80]}"


# ─────────────────────────────────────────────────────────────────
#  DEMO RESPONSES (all 16 conditions)
# ─────────────────────────────────────────────────────────────────

def _demo(text):
    t = text.lower()
    cond = detect_condition(t)
    demos = {
        "anxiety":        ("That anxious feeling can be so consuming — like your thoughts are racing faster than you can catch them. What you're experiencing makes complete sense, and it's your nervous system trying to protect you. Try this right now: breathe in for 4 counts, hold for 7, out for 8. It activates the parasympathetic system in under a minute. What do you think is the root of this anxiety?",
                           {"stress":6.5,"energy":0.78,"pace":158,"emotion":"anxious","condition":"anxiety","insight":"GAD presentation. 4-7-8 breathing recommended. Explore triggers.","psycho":"Anxiety activates the amygdala. The 4-7-8 breath reverses cortisol response physiologically in under 60 seconds.","crisis":False}),
        "depression":     ("Feeling that weight is one of the hardest things to carry — and yet here you are, reaching out, which takes courage. You don't have to make sense of everything right now. Has this heaviness been building for a while, or did something specific change recently?",
                           {"stress":5.2,"energy":0.38,"pace":112,"emotion":"sad","condition":"depression","insight":"Low mood, reduced energy. PHQ-9 screening recommended. Monitor for MDD criteria.","psycho":"Low mood depletes dopamine. Even 10 minutes of physical movement increases dopamine by up to 30%.","crisis":False}),
        "ocd":            ("Those intrusive thoughts are exhausting to live with — and I want you to know that the thought itself doesn't reflect who you are or what you want. OCD hijacks your threat-detection system. The key is to notice the urge without acting on it — even for 5 minutes. What kind of thoughts or urges feel most overwhelming right now?",
                           {"stress":6.8,"energy":0.65,"pace":145,"emotion":"anxious","condition":"ocd","insight":"OCD intrusive thought presentation. ERP psychoeducation appropriate. Avoid providing reassurance.","psycho":"OCD is maintained by rituals that temporarily reduce anxiety. ERP — facing the anxiety without the ritual — breaks this cycle with 60-80% effectiveness.","crisis":False}),
        "ptsd":           ("Thank you for trusting me with this. You don't need to share any details you're not ready to — we can go at whatever pace feels safe. Right now, can you feel your feet on the floor and name 3 things you can see around you? Let's get grounded first.",
                           {"stress":7.5,"energy":0.45,"pace":118,"emotion":"fearful","condition":"ptsd","insight":"Possible PTSD. Prioritise grounding and safety. Do not push for trauma narrative.","psycho":"Trauma activates the survival brain. Grounding techniques reconnect the prefrontal cortex, reducing flashback intensity within minutes.","crisis":False}),
        "bipolar":        ("What you're describing sounds like a real shift in your energy and mood — and it's important to pay attention to these changes. Tracking your sleep is one of the most powerful early warning signs for mood episodes. How has your sleep been over the last week?",
                           {"stress":5.5,"energy":0.88,"pace":175,"emotion":"overwhelmed","condition":"bipolar","insight":"Possible hypomanic features. Sleep monitoring critical. Check medication adherence.","psycho":"In Bipolar Disorder, sleep disruption is both a trigger and early warning sign. Even one night of missed sleep can destabilise mood regulation.","crisis":False}),
        "panic":          ("A panic attack is terrifying in the moment — your body is flooded with signals that feel like danger even when you're physically safe. The most important thing: it will always pass. Try breathing out slowly — longer exhale than inhale. Did this come on suddenly or did you feel it building?",
                           {"stress":8.2,"energy":0.92,"pace":182,"emotion":"fearful","condition":"panic","insight":"Panic attack presentation. Psychoeducation on panic cycle essential. Diaphragmatic breathing immediate intervention.","psycho":"Panic attacks always peak within 10 minutes and pass. The adrenaline will be naturally metabolised — your body knows how to recover.","crisis":False}),
        "social_anxiety": ("The fear of being judged makes every interaction feel like a high-stakes performance — that's exhausting to carry constantly. What you feel makes sense, even if the fear is bigger than the actual risk. What social situation feels most overwhelming for you right now?",
                           {"stress":5.8,"energy":0.52,"pace":128,"emotion":"anxious","condition":"social_anxiety","insight":"Social Anxiety Disorder. Exposure hierarchy and cognitive restructuring indicated.","psycho":"Social anxiety involves overestimating how much others notice our mistakes. Research shows people are far less focused on us than we believe.","crisis":False}),
        "eating_disorder":("The relationship with food and your body can be one of the most complex struggles a person can have. You're not alone, and it takes real courage to speak about it. I want this to be a safe space. What's been feeling most difficult lately — around eating, your body, or both?",
                           {"stress":6.0,"energy":0.42,"pace":120,"emotion":"sad","condition":"eating_disorder","insight":"Possible eating disorder. Body-neutral language essential. Refer to specialist service.","psycho":"Eating disorders have the highest mortality of any mental health condition. Recovery is absolutely possible with the right specialist support.","crisis":False}),
        "adhd":           ("That struggle to focus, the feeling that your brain just won't cooperate — it's real, and it's not laziness or a character flaw. The ADHD brain is wired differently, not broken. Try this: break the task into the tiniest possible first step. What's the one thing you're finding hardest to start?",
                           {"stress":5.0,"energy":0.75,"pace":168,"emotion":"overwhelmed","condition":"adhd","insight":"ADHD executive function difficulties. Task initiation and working memory challenges. Practical scaffolding recommended.","psycho":"ADHD involves dopamine dysregulation, not attention deficit. External structure and novelty help activate the brain's focus system.","crisis":False}),
        "grief":          ("Grief is one of the most profound human experiences — and there's no right way, no timeline, no finish line. What you feel is real and deserves space. Would you like to tell me a little about the person or thing you've lost, if you feel ready?",
                           {"stress":5.5,"energy":0.35,"pace":108,"emotion":"sad","condition":"grief","insight":"Acute grief. No timeline pressure. Meaning-making approach when patient is ready.","psycho":"Grief is not a problem to solve or stages to complete. It changes shape over time — it doesn't disappear, it integrates into who you become.","crisis":False}),
        "burnout":        ("What you're describing is burnout — and I want to be clear: this is not weakness, it's what happens when a person gives more than their system can sustain for too long. When did you last feel like yourself, not just a function at work?",
                           {"stress":7.8,"energy":0.22,"pace":105,"emotion":"tired","condition":"burnout","insight":"Severe burnout. Immediate rest and boundary-setting critical. Systemic factors to explore.","psycho":"Burnout requires active recovery, not just absence from work. The nervous system needs deliberate repair — not just stopping, but rebuilding.","crisis":False}),
        "sleep":          ("Sleep problems and emotional health are deeply connected — when one suffers, the other follows. The most evidence-based approach is CBT for Insomnia (CBT-I), which is more effective long-term than sleep medication. Is it harder to fall asleep, stay asleep, or do you wake too early?",
                           {"stress":4.5,"energy":0.28,"pace":118,"emotion":"tired","condition":"sleep","insight":"Insomnia presentation. CBT-I protocol recommended. Rule out sleep apnea.","psycho":"Sleep restriction therapy — temporarily reducing time in bed — is counterintuitive but highly effective for rebuilding sleep drive.","crisis":False}),
        "addiction":      ("It takes real honesty and courage to name this. Addiction isn't a moral failing — it's a brain condition where the reward system has been hijacked. Craving is not weakness. What does a typical day look like around this for you?",
                           {"stress":6.5,"energy":0.55,"pace":138,"emotion":"overwhelmed","condition":"addiction","insight":"Substance use presentation. Motivational interviewing approach. HALT check and trigger mapping recommended.","psycho":"Addiction creates physical changes in the prefrontal cortex that impair impulse control. Recovery literally rebuilds these neural pathways over time.","crisis":False}),
        "bpd":            ("The intensity of what you feel is real — emotions that big are exhausting to carry. DBT was built specifically for this experience. The TIPP skill — Temperature, Intense exercise, Paced breathing, Progressive relaxation — can help when emotions feel unbearable. What's happening right now that's bringing this up?",
                           {"stress":7.2,"energy":0.82,"pace":165,"emotion":"overwhelmed","condition":"bpd","insight":"BPD features. DBT skills appropriate. Validate emotion without reinforcing crisis behaviour.","psycho":"DBT was developed for emotional dysregulation and has strong evidence — 77% reduction in self-harm in clinical trials.","crisis":False}),
        "schizophrenia":  ("I hear you, and I want you to know I'm right here with you. What you're experiencing sounds frightening and confusing, and I want to help. The most important thing right now is that you're safe. Is there someone with you, or someone you can call to be with you?",
                           {"stress":8.0,"energy":0.50,"pace":125,"emotion":"fearful","condition":"schizophrenia","insight":"Possible psychotic symptoms. Urgent clinical referral needed. Do not challenge delusions. Safety assessment priority.","psycho":"Psychosis is a medical condition involving brain chemistry changes. With the right treatment, most people make significant recovery.","crisis":True}),
        "phobia":         ("Specific phobias are incredibly common — and the brain has learned to treat something as danger even when it isn't. The good news is that phobias respond very well to treatment. Graduated exposure — approaching the fear in small steps — is highly effective. What happens in your body when you encounter or think about it?",
                           {"stress":6.0,"energy":0.68,"pace":148,"emotion":"fearful","condition":"phobia","insight":"Specific phobia. Graduated exposure hierarchy appropriate.","psycho":"Phobias are maintained by avoidance. Each time you avoid, the brain confirms danger. Gradual exposure breaks this cycle.","crisis":False}),
    }
    if cond in demos:
        reply, bio = demos[cond]
        return {"reply":reply,"biomarkers":bio,"crisis":bool(bio.get("crisis"))}
    return {"reply":"Thank you for sharing that with me — whatever brought you here today, you're not alone. I'm here to listen without judgement. Can you tell me a little more about what's been on your mind?",
            "biomarkers":{"stress":3.0,"energy":0.60,"pace":130,"emotion":"neutral","condition":"general","insight":"Initial assessment. Exploring presenting concerns.","psycho":PSYCHO_FACTS[now_ts()%len(PSYCHO_FACTS)],"crisis":False},"crisis":False}


# ─────────────────────────────────────────────────────────────────
#  BUILD CONDITION CARDS HTML (called once at startup)
# ─────────────────────────────────────────────────────────────────

def _cond_cards():
    out = ""
    for key, c in PSYCH_CONDITIONS.items():
        syms = "".join(f"<li>{s}</li>" for s in c["symptoms"][:4])
        techs = "".join(f'<span class="tech-chip">{t}</span>' for t in c["techniques"][:3])
        out += f"""<div class="cond-card" id="cc-{key}" data-key="{key}" onclick="selectCond('{key}')">
  <div class="cond-icon">{c["icon"]}</div>
  <div class="cond-body">
    <div class="cond-name">{c["name"]}</div>
    <div class="cond-desc">{c["description"]}</div>
    <ul class="cond-syms">{syms}</ul>
    <div class="cond-techs">{techs}</div>
  </div>
  <div class="cond-scale">{c["phq_scale"]}</div>
</div>"""
    return out


# ─────────────────────────────────────────────────────────────────
#  FRONTEND HTML
# ─────────────────────────────────────────────────────────────────

CONDITIONS_JS = json.dumps({k: {"name":v["name"],"icon":v["icon"],"color":v["color"],
    "symptoms":v["symptoms"],"techniques":v["techniques"],"phq_scale":v["phq_scale"],
    "description":v["description"]} for k,v in PSYCH_CONDITIONS.items()})

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MindWell — Mental Health AI Platform</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,400;1,300;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#07080f;--s1:#0d0f1a;--s2:#131525;--s3:#1a1d30;--s4:#222640;--accent:#5b6ef5;--a2:#8b9bf8;--glow:rgba(91,110,245,.18);--green:#2dd4a0;--amber:#f0b429;--coral:#f26a5e;--text:#d8ddf5;--sub:#636882;--muted:#3d4162;--border:rgba(255,255,255,.055);--r:14px;--font:'Plus Jakarta Sans',sans-serif;--serif:'Fraunces',serif}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--font);overflow:hidden}
body::before{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;opacity:.4;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.025'/%3E%3C/svg%3E")}
.blob{position:fixed;top:-100px;left:50%;transform:translateX(-50%);width:700px;height:500px;border-radius:50%;pointer-events:none;z-index:0;background:radial-gradient(ellipse at 50% 30%,rgba(91,110,245,.07) 0%,transparent 65%)}
.app{display:flex;height:100vh;position:relative;z-index:1;padding-top:52px}

nav{position:fixed;top:0;left:0;right:0;height:52px;z-index:300;background:rgba(7,8,15,.92);backdrop-filter:blur(24px);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 18px}
.logo{font-family:var(--serif);font-size:20px;font-style:italic;font-weight:300;color:var(--a2)}
.logo b{font-style:normal;color:var(--text);font-weight:400}
.nav-r{display:flex;align-items:center;gap:7px}
.pill{display:flex;border-radius:20px;border:1px solid var(--border);background:var(--s2);overflow:hidden}
.pill button{font-family:var(--font);font-size:11px;font-weight:500;padding:5px 12px;border:none;background:transparent;color:var(--sub);cursor:pointer;transition:.18s}
.pill button.on{background:var(--accent);color:#fff}
.pill.lang button.on{background:rgba(91,110,245,.28);color:var(--a2)}
.ai-badge{font-size:10px;padding:3px 9px;border-radius:20px;border:1px solid rgba(242,106,94,.3);background:rgba(242,106,94,.1);color:var(--coral)}
.ai-badge.live{border-color:rgba(45,212,160,.3);background:rgba(45,212,160,.1);color:var(--green)}

#api-banner{position:fixed;top:52px;left:0;right:0;z-index:200;background:linear-gradient(90deg,rgba(91,110,245,.12),rgba(139,155,248,.06));border-bottom:1px solid rgba(91,110,245,.18);padding:8px 18px;font-size:12px;color:var(--a2);display:flex;align-items:center;gap:9px;flex-wrap:wrap}
.api-in{flex:1;min-width:180px;max-width:270px;background:var(--s3);border:1px solid var(--border);border-radius:8px;padding:5px 10px;color:var(--text);font-family:var(--font);font-size:12px;outline:none;transition:.2s}
.api-in:focus{border-color:var(--accent)}
.api-btn{padding:5px 13px;border:none;border-radius:8px;font-family:var(--font);font-size:12px;cursor:pointer;transition:.18s;font-weight:500}
.api-btn.p{background:var(--accent);color:#fff}
.api-btn.g{background:var(--s4);color:var(--sub)}

.sidebar{width:242px;flex-shrink:0;border-right:1px solid var(--border);background:var(--s1);display:flex;flex-direction:column;overflow:hidden}
.stabs{display:flex;border-bottom:1px solid var(--border);flex-shrink:0}
.stab{flex:1;padding:10px 0;font-size:11px;font-weight:500;text-align:center;background:none;border:none;color:var(--sub);cursor:pointer;transition:.18s;font-family:var(--font);border-bottom:2px solid transparent}
.stab.on{color:var(--a2);border-bottom-color:var(--accent)}
.sc{flex:1;overflow-y:auto;padding:13px}
.sc::-webkit-scrollbar{width:3px}
.sc::-webkit-scrollbar-thumb{background:var(--s3);border-radius:3px}
.sec-l{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px}

.mood-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;margin-bottom:6px}
.mb{aspect-ratio:1;border-radius:9px;border:1px solid var(--border);background:var(--s2);font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.18s}
.mb:hover{border-color:var(--accent);transform:scale(1.08)}
.mb.on{border-color:var(--accent);background:var(--glow)}
.mood-lbl{font-size:11px;color:var(--sub);text-align:center;margin-bottom:12px;min-height:15px}

.score-card{background:var(--s2);border-radius:var(--r);border:1px solid var(--border);padding:11px 12px;margin-bottom:12px}
.sc-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:4px}
.sc-name{font-size:11px;color:var(--sub)}
.sc-val{font-size:12px;font-weight:600}
.sc-bg{height:3px;background:rgba(255,255,255,.04);border-radius:3px;overflow:hidden;margin-bottom:8px}
.sc-fg{height:100%;border-radius:3px;transition:width .7s ease}

.hist{padding:8px 10px;border-radius:10px;border:1px solid var(--border);background:var(--s2);margin-bottom:5px;cursor:pointer;transition:.18s}
.hist:hover{border-color:var(--accent)}
.hist-date{font-size:10px;color:var(--sub)}
.hist-prev{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}

.cond-card{display:flex;align-items:flex-start;gap:9px;padding:9px 10px;border-radius:10px;border:1px solid var(--border);background:var(--s2);margin-bottom:5px;cursor:pointer;transition:.18s;position:relative}
.cond-card:hover{border-color:var(--accent);background:var(--s3)}
.cond-card.active{border-color:var(--accent);background:var(--glow)}
.cond-icon{font-size:19px;flex-shrink:0;margin-top:1px}
.cond-body{flex:1;min-width:0}
.cond-name{font-size:12px;font-weight:600;margin-bottom:1px}
.cond-desc{font-size:10px;color:var(--sub);line-height:1.4;margin-bottom:4px}
.cond-syms{font-size:10px;color:var(--sub);padding-left:13px;display:none;line-height:1.8}
.cond-techs{display:none;flex-wrap:wrap;gap:4px;margin-top:5px}
.tech-chip{font-size:9px;padding:2px 7px;border-radius:20px;border:1px solid rgba(91,110,245,.25);color:var(--a2);background:rgba(91,110,245,.08)}
.cond-card.active .cond-syms{display:block}
.cond-card.active .cond-techs{display:flex}
.cond-scale{font-size:9px;padding:2px 6px;border-radius:4px;background:var(--s4);color:var(--sub);flex-shrink:0;align-self:flex-start}

.chat{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}
.messages{flex:1;overflow-y:auto;padding:18px 20px;display:flex;flex-direction:column;gap:12px}
.messages::-webkit-scrollbar{width:3px}
.messages::-webkit-scrollbar-thumb{background:var(--s3);border-radius:3px}

.msg{max-width:76%;animation:up .22s ease}
@keyframes up{from{opacity:0;transform:translateY(9px)}to{opacity:1;transform:none}}
.msg.u{align-self:flex-end}
.msg.a{align-self:flex-start}
.bubble{padding:11px 14px;border-radius:16px;font-size:14px;line-height:1.75}
.msg.u .bubble{background:var(--accent);color:#fff;border-bottom-right-radius:3px}
.msg.a .bubble{background:var(--s1);border:1px solid var(--border);color:var(--text);border-bottom-left-radius:3px}
.msg-time{font-size:10px;color:var(--sub);margin-top:3px;padding:0 3px}
.msg.u .msg-time{text-align:right}
.e-badge{display:inline-flex;align-items:center;gap:4px;font-size:10px;font-weight:500;padding:2px 8px;border-radius:20px;margin-bottom:5px;background:rgba(91,110,245,.12);border:1px solid rgba(91,110,245,.22);color:var(--a2)}
.e-dot{width:4px;height:4px;border-radius:50%;background:var(--a2)}
.cond-banner{display:inline-flex;align-items:center;gap:6px;padding:5px 11px;border-radius:10px;margin-bottom:7px;font-size:12px;border:1px solid rgba(91,110,245,.25);background:rgba(91,110,245,.1);color:var(--a2);font-weight:500}

.typing{align-self:flex-start;display:none;gap:5px;align-items:center;padding:11px 14px;background:var(--s1);border:1px solid var(--border);border-radius:16px;border-bottom-left-radius:3px}
.typing.show{display:flex}
.dot{width:5px;height:5px;border-radius:50%;background:var(--sub);animation:bop .8s infinite}
.dot:nth-child(2){animation-delay:.15s}.dot:nth-child(3){animation-delay:.3s}
@keyframes bop{0%,80%,100%{transform:none}40%{transform:translateY(-5px)}}

.welcome{display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;text-align:center;padding:36px 28px;gap:9px}
.w-icon{font-size:54px;margin-bottom:4px;filter:drop-shadow(0 0 20px rgba(91,110,245,.3))}
.w-title{font-family:var(--serif);font-size:27px;font-weight:300;font-style:italic}
.w-sub{font-size:13px;color:var(--sub);max-width:320px;line-height:1.85;margin-top:2px}
.w-chips{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;margin-top:14px}
.w-chip{font-size:12px;padding:7px 15px;border-radius:20px;border:1px solid var(--border);background:var(--s1);color:var(--sub);cursor:pointer;transition:.2s;font-family:var(--font)}
.w-chip:hover{border-color:var(--accent);color:var(--a2);background:var(--glow)}

.input-zone{padding:10px 18px 14px;border-top:1px solid var(--border);background:var(--bg);flex-shrink:0}
.emotion-row{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:8px;align-items:center}
.ec-l{font-size:10px;color:var(--sub)}
.chip{font-size:11px;padding:3px 10px;border-radius:20px;border:1px solid var(--border);background:var(--s2);color:var(--sub);cursor:pointer;transition:.18s;font-family:var(--font)}
.chip:hover,.chip.on{border-color:var(--accent);color:var(--a2);background:var(--glow)}
.irow{display:flex;align-items:flex-end;gap:7px;background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:8px 10px;transition:.2s}
.irow:focus-within{border-color:var(--accent)}
#inp{flex:1;background:none;border:none;outline:none;color:var(--text);font-family:var(--font);font-size:14px;resize:none;max-height:100px;min-height:22px;line-height:1.55}
#inp::placeholder{color:var(--sub)}
.ico{width:31px;height:31px;border-radius:9px;border:1px solid var(--border);background:var(--s2);color:var(--sub);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.18s;flex-shrink:0;font-size:15px}
.ico:hover{border-color:var(--accent);color:var(--a2)}
.ico.rec{border-color:var(--coral);color:var(--coral);animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.send-btn{width:31px;height:31px;border-radius:9px;border:none;background:var(--accent);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px;transition:.18s}
.send-btn:hover{background:var(--a2);transform:scale(1.06)}
.send-btn:disabled{opacity:.3;cursor:not-allowed;transform:none}

.bio-panel{width:220px;flex-shrink:0;border-left:1px solid var(--border);background:var(--s1);padding:14px;overflow-y:auto;display:flex;flex-direction:column;gap:14px}
.bio-panel::-webkit-scrollbar{width:3px}
.bio-panel::-webkit-scrollbar-thumb{background:var(--s3);border-radius:3px}
.bp-sec{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:8px}
.bm-card{background:var(--s2);border-radius:var(--r);border:1px solid var(--border);padding:10px 12px;margin-bottom:7px}
.bm-lbl{font-size:10px;color:var(--sub)}
.bm-val{font-size:24px;font-weight:600;margin:2px 0 1px;font-variant-numeric:tabular-nums}
.bm-desc{font-size:10px;color:var(--sub);line-height:1.4}
.status-box{border-radius:10px;padding:8px 10px;font-size:11px;line-height:1.6;border:1px solid}
.s-calm{border-color:rgba(45,212,160,.3);background:rgba(45,212,160,.07);color:var(--green)}
.s-warn{border-color:rgba(240,180,41,.3);background:rgba(240,180,41,.07);color:var(--amber)}
.s-crisis{border-color:rgba(242,106,94,.3);background:rgba(242,106,94,.07);color:var(--coral)}
.txt-sm{font-size:12px;color:var(--sub);line-height:1.72}
.ac-card{background:var(--s2);border-radius:var(--r);border:1px solid var(--border);padding:11px 12px}
.ac-hdr{display:flex;align-items:center;gap:7px;margin-bottom:7px}
.ac-icon{font-size:20px}
.ac-name{font-size:13px;font-weight:600;flex:1}
.ac-badge{font-size:9px;padding:2px 6px;border-radius:4px;background:var(--s4);color:var(--sub)}
.ac-syms{font-size:10px;color:var(--sub);padding-left:13px;line-height:1.9}
.ac-techs{display:flex;flex-wrap:wrap;gap:4px;margin-top:7px}
.ac-tech{font-size:10px;padding:2px 7px;border-radius:20px;border:1px solid rgba(91,110,245,.25);color:var(--a2);background:rgba(91,110,245,.08)}

#doc-view{display:none;flex:1;overflow-y:auto;padding:18px 20px;flex-direction:column;gap:14px}
#doc-view.show{display:flex}
#conds-view{display:none;flex:1;overflow-y:auto;padding:18px 20px}
.enc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;margin-top:14px}
.enc-card{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:14px;cursor:pointer;transition:.18s}
.enc-card:hover{border-color:var(--accent);background:var(--s2)}
.enc-icon{font-size:28px;margin-bottom:7px}
.enc-name{font-size:13px;font-weight:600;margin-bottom:3px}
.enc-desc{font-size:11px;color:var(--sub);line-height:1.6;margin-bottom:7px}
.enc-tag{font-size:10px;padding:2px 7px;border-radius:4px;background:var(--s3);color:var(--sub);display:inline-block}
.doc-h{font-family:var(--serif);font-size:24px;font-weight:300;font-style:italic;padding-top:4px}
.doc-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px}
.doc-card{background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:14px}
.dc-h{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--sub);margin-bottom:10px}
.p-row{display:flex;align-items:center;gap:9px;padding:8px 0;border-bottom:1px solid var(--border);cursor:pointer}
.p-row:last-child{border-bottom:none}
.av{width:30px;height:30px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;background:var(--glow);color:var(--a2)}
.p-nm{font-size:13px;font-weight:500}.p-st{font-size:11px;color:var(--sub)}
.sdot{width:6px;height:6px;border-radius:50%;flex-shrink:0;margin-left:auto}
.sdot.g{background:var(--green)}.sdot.a{background:var(--amber)}.sdot.r{background:var(--coral)}
.phq-r{display:flex;align-items:center;margin-bottom:7px;gap:7px}
.phq-q{font-size:11px;color:var(--sub);flex:1}
.phq-sc{display:flex;gap:3px}
.ps{width:24px;height:24px;border-radius:7px;border:1px solid var(--border);background:var(--s2);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:500;cursor:pointer;transition:.18s;color:var(--sub)}
.ps:hover,.ps.on{border-color:var(--accent);background:var(--glow);color:var(--a2)}
.phq-tot{margin-top:9px;padding-top:9px;border-top:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.summary-box{background:rgba(91,110,245,.06);border-left:3px solid var(--accent);padding:12px 14px;border-radius:4px;font-size:13px;line-height:1.82}

.modal-bg{display:none;position:fixed;inset:0;z-index:600;background:rgba(0,0,0,.8);backdrop-filter:blur(6px);align-items:center;justify-content:center}
.modal-bg.show{display:flex}
.modal{background:var(--s1);border:1px solid rgba(242,106,94,.25);border-radius:20px;padding:26px;max-width:340px;width:92%;text-align:center;animation:up .3s ease}
.modal h2{font-family:var(--serif);font-size:22px;font-style:italic;font-weight:300;color:var(--coral);margin:8px 0 7px}
.modal p{font-size:13px;color:var(--sub);line-height:1.8}
.helpline{background:rgba(242,106,94,.09);border:1px solid rgba(242,106,94,.18);border-radius:10px;padding:8px 12px;margin:8px 0;font-size:12px;color:var(--coral)}
.helpline strong{display:block;font-size:15px;letter-spacing:.05em;margin-top:1px}
.mc{width:100%;padding:10px;background:var(--accent);border:none;border-radius:10px;color:#fff;font-family:var(--font);font-size:14px;cursor:pointer;font-weight:500;margin-top:5px;transition:.18s}
.mc:hover{background:var(--a2)}

@media(max-width:960px){.sidebar{display:none}}
@media(max-width:720px){.bio-panel{display:none}}
@media(max-width:560px){.doc-grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="blob"></div>

<div id="api-banner">
  <span>🔑 Google Gemini API key for live AI (free at aistudio.google.com) — or skip for demo:</span>
  <input class="api-in" id="api-key-input" type="password" placeholder="AIza...">
  <button class="api-btn p" onclick="saveKey()">Connect AI</button>
  <button class="api-btn g" onclick="skipKey()">Demo Mode</button>
</div>

<nav>
  <div class="logo">Mind<b>Well</b></div>
  <div class="nav-r">
    <div class="ai-badge" id="ai-badge">● Demo</div>
    <div class="pill lang" id="lang-pill">
      <button class="on" onclick="setLang('en',this)">EN</button>
      <button onclick="setLang('hi',this)">हिं</button>
      <button onclick="setLang('mr',this)">मर</button>
      <button onclick="setLang('ta',this)">தமி</button>
    </div>
    <div class="pill">
      <button class="on" id="btn-chat" onclick="setMode('chat')">Chat</button>
      <button id="btn-cond" onclick="setMode('conditions')">Conditions</button>
      <button id="btn-doc"  onclick="setMode('doctor')">Doctor</button>
    </div>
  </div>
</nav>

<div class="app">
  <div class="sidebar" id="sidebar">
    <div class="stabs">
      <button class="stab on" onclick="switchTab('mood',this)">Mood</button>
      <button class="stab"    onclick="switchTab('history',this)">History</button>
      <button class="stab"    onclick="switchTab('conds',this)">Conditions</button>
    </div>
    <div class="sc" id="tab-mood">
      <div class="sec-l">How are you feeling?</div>
      <div class="mood-grid">
        <button class="mb" onclick="pickMood(this,'😊','Happy')"       title="Happy">😊</button>
        <button class="mb" onclick="pickMood(this,'😔','Sad')"         title="Sad">😔</button>
        <button class="mb" onclick="pickMood(this,'😰','Anxious')"     title="Anxious">😰</button>
        <button class="mb" onclick="pickMood(this,'😤','Frustrated')"  title="Frustrated">😤</button>
        <button class="mb" onclick="pickMood(this,'😐','Neutral')"     title="Neutral">😐</button>
        <button class="mb" onclick="pickMood(this,'😴','Tired')"       title="Tired">😴</button>
        <button class="mb" onclick="pickMood(this,'😡','Angry')"       title="Angry">😡</button>
        <button class="mb" onclick="pickMood(this,'🥺','Lonely')"      title="Lonely">🥺</button>
        <button class="mb" onclick="pickMood(this,'🤯','Overwhelmed')" title="Overwhelmed">🤯</button>
        <button class="mb" onclick="pickMood(this,'😌','Calm')"        title="Calm">😌</button>
      </div>
      <div class="mood-lbl" id="mood-lbl">Select your mood</div>
      <div class="sec-l">Wellbeing today</div>
      <div class="score-card">
        <div class="sc-row"><span class="sc-name">Anxiety</span><span class="sc-val" id="anx-v" style="color:var(--amber)">4.0</span></div>
        <div class="sc-bg"><div class="sc-fg" id="anx-b" style="width:40%;background:var(--amber)"></div></div>
        <div class="sc-row"><span class="sc-name">Mood</span><span class="sc-val" id="mood-v" style="color:var(--green)">7.0</span></div>
        <div class="sc-bg"><div class="sc-fg" id="mood-b" style="width:70%;background:var(--green)"></div></div>
        <div class="sc-row"><span class="sc-name">Stress</span><span class="sc-val" id="stress-v" style="color:var(--a2)">3.0</span></div>
        <div class="sc-bg"><div class="sc-fg" id="stress-b" style="width:30%;background:var(--a2)"></div></div>
      </div>
    </div>
    <div class="sc" id="tab-history" style="display:none">
      <div class="sec-l">Recent sessions</div>
      <div class="hist" onclick="loadHist('30May')"><div class="hist-date">30 May 2026</div><div class="hist-prev">Work stress and sleep issues…</div></div>
      <div class="hist" onclick="loadHist('28May')"><div class="hist-date">28 May 2026</div><div class="hist-prev">Feeling better after the weekend…</div></div>
      <div class="hist" onclick="loadHist('25May')"><div class="hist-date">25 May 2026</div><div class="hist-prev">Exam anxiety and pressure…</div></div>
      <div class="hist" onclick="loadHist('22May')"><div class="hist-date">22 May 2026</div><div class="hist-prev">OCD intrusive thoughts flaring…</div></div>
      <div class="hist" onclick="loadHist('18May')"><div class="hist-date">18 May 2026</div><div class="hist-prev">Low mood, no motivation…</div></div>
    </div>
    <div class="sc" id="tab-conds" style="display:none">
      <div class="sec-l">Select condition</div>
      CONDITION_CARDS_PLACEHOLDER
    </div>
  </div>

  <div class="chat" id="chat-area">
    <div id="chat-view" style="display:flex;flex-direction:column;flex:1;overflow:hidden">
      <div class="messages" id="msgs">
        <div class="welcome" id="welcome">
          <div class="w-icon">🧠</div>
          <div class="w-title">Hello, how are you today?</div>
          <div class="w-sub">Expert support across 16 psychological conditions — trained with clinical knowledge. Everything you share stays private.</div>
          <div class="w-chips">
            <div class="w-chip" onclick="qs('I have been feeling very anxious and cannot stop worrying')">😰 Anxiety</div>
            <div class="w-chip" onclick="qs('I feel very low and hopeless about everything')">😔 Depression</div>
            <div class="w-chip" onclick="qs('I keep having intrusive thoughts I cannot control')">🔄 OCD</div>
            <div class="w-chip" onclick="qs('I had a panic attack today and I am scared')">💨 Panic</div>
            <div class="w-chip" onclick="qs('I am so burned out from work I cannot function')">🔥 Burnout</div>
            <div class="w-chip" onclick="qs('I cannot sleep at all no matter what I try')">😴 Sleep</div>
            <div class="w-chip" onclick="qs('I am dealing with grief after losing someone close')">🕊️ Grief</div>
            <div class="w-chip" onclick="qs('I feel lonely and completely disconnected from everyone')">🥺 Loneliness</div>
          </div>
        </div>
      </div>
      <div class="typing" id="typing"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
      <div class="input-zone">
        <div class="emotion-row">
          <span class="ec-l">Feeling:</span>
          <div class="chip" onclick="toggleChip(this)">Anxious</div>
          <div class="chip" onclick="toggleChip(this)">Sad</div>
          <div class="chip" onclick="toggleChip(this)">Angry</div>
          <div class="chip" onclick="toggleChip(this)">Confused</div>
          <div class="chip" onclick="toggleChip(this)">Hopeful</div>
          <div class="chip" onclick="toggleChip(this)">Overwhelmed</div>
          <div class="chip" onclick="toggleChip(this)">Numb</div>
        </div>
        <div class="irow">
          <textarea id="inp" rows="1" placeholder="Type how you're feeling… or tap 🎙️ to speak" onkeydown="onKey(event)" oninput="rsz(this)"></textarea>
          <button class="ico" id="mic-btn" onclick="toggleMic()" title="Voice input">🎙️</button>
          <button class="send-btn" id="send-btn" onclick="sendMsg()">➤</button>
        </div>
      </div>
    </div>

    <div id="conds-view">
      <div style="font-family:var(--serif);font-size:24px;font-weight:300;font-style:italic">16 Psychological Conditions</div>
      <div style="font-size:13px;color:var(--sub);margin-top:6px">Click any condition to start a guided conversation</div>
      <div class="enc-grid" id="enc-grid"></div>
    </div>

    <div id="doc-view">
      <div class="doc-h">Clinical Dashboard</div>
      <div class="doc-grid">
        <div class="doc-card">
          <div class="dc-h">Active patients</div>
          <div class="p-row"><div class="av">RK</div><div><div class="p-nm">Raj Kumar</div><div class="p-st">Anxiety · GAD-7: 14 · Today</div></div><div class="sdot a"></div></div>
          <div class="p-row"><div class="av">PS</div><div><div class="p-nm">Priya Sharma</div><div class="p-st">Depression · PHQ-9: 12 · Yesterday</div></div><div class="sdot g"></div></div>
          <div class="p-row"><div class="av">AM</div><div><div class="p-nm">Aryan Mehta</div><div class="p-st">OCD · OCI-R: 28 · 3 days ago</div></div><div class="sdot r"></div></div>
          <div class="p-row"><div class="av">SJ</div><div><div class="p-nm">Sneha Joshi</div><div class="p-st">PTSD · PCL-5: 38 · Today</div></div><div class="sdot g"></div></div>
          <div class="p-row"><div class="av">VK</div><div><div class="p-nm">Vikram Kapoor</div><div class="p-st">Bipolar · MDQ: 8 · Yesterday</div></div><div class="sdot a"></div></div>
        </div>
        <div class="doc-card">
          <div class="dc-h">PHQ-9 Assessment</div>
          <div class="phq-r"><span class="phq-q">Little interest or pleasure</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
          <div class="phq-r"><span class="phq-q">Feeling down or hopeless</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
          <div class="phq-r"><span class="phq-q">Trouble sleeping</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
          <div class="phq-r"><span class="phq-q">Feeling tired or low energy</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
          <div class="phq-r"><span class="phq-q">Poor appetite or overeating</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
          <div class="phq-r"><span class="phq-q">Feeling bad about yourself</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
          <div class="phq-r"><span class="phq-q">Trouble concentrating</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
          <div class="phq-r"><span class="phq-q">Moving or speaking slowly/restless</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
          <div class="phq-r"><span class="phq-q">Thoughts of self-harm</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
          <div class="phq-tot"><span style="font-size:12px;color:var(--sub)">PHQ-9 Total</span><span style="font-size:22px;font-weight:600;color:var(--amber)" id="phq-t">0</span></div>
        </div>
        <div class="doc-card" style="grid-column:1/-1">
          <div class="dc-h">AI Session Summary — Raj Kumar</div>
          <div class="summary-box" id="doc-summary">
            <b style="color:var(--a2)">Chief Complaint:</b> Elevated work-related stress, difficulty concentrating, disrupted sleep ×2 weeks. Panic features during presentations.<br><br>
            <b style="color:var(--a2)">Emotional Trajectory:</b> Session began anxious → progressed to reflective → ended calmer after breathing exercise. Positive therapeutic arc.<br><br>
            <b style="color:var(--a2)">Possible Condition(s):</b> GAD with panic features (GAD-7: 14 = moderate-severe). Rule out comorbid MDD. Sleep disturbance secondary to anxiety.<br><br>
            <b style="color:var(--a2)">Risk Level:</b> Low. No suicidal ideation. Good insight and help-seeking behaviour present.<br><br>
            <b style="color:var(--a2)">Recommended Actions:</b> Introduce 4-7-8 breathing. CBT thought records for catastrophising. Sleep hygiene education. PHQ-9 reassessment in 2 weeks.
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="bio-panel" id="bio-panel">
    <div>
      <div class="bp-sec">Active condition</div>
      <div class="ac-card" id="ac-panel">
        <div class="ac-hdr"><span class="ac-icon">🧠</span><span class="ac-name">General Support</span></div>
        <div class="txt-sm">Start chatting or select a condition — I'll detect it automatically.</div>
      </div>
    </div>
    <div>
      <div class="bp-sec">Voice biomarker</div>
      <div class="bm-card"><div class="bm-lbl">Stress index</div><div class="bm-val" id="bm-s" style="color:var(--amber)">3.2</div><div class="bm-desc" id="bm-sd">Moderate tension</div></div>
      <div class="bm-card"><div class="bm-lbl">Emotional energy</div><div class="bm-val" id="bm-e" style="color:var(--a2)">0.60</div><div class="bm-desc">Normal level</div></div>
      <div class="bm-card"><div class="bm-lbl">Speech pace</div><div class="bm-val" id="bm-p" style="color:var(--green)">132</div><div class="bm-desc">wpm — relaxed</div></div>
    </div>
    <div><div class="bp-sec">Status</div><div class="status-box s-calm" id="status-box">✅ All signals normal</div></div>
    <div><div class="bp-sec">Session insight</div><div class="txt-sm" id="insight-txt">Insights appear as session develops.</div></div>
    <div><div class="bp-sec">Psychoeducation</div><div class="txt-sm" id="psycho-txt">Anxiety activates the amygdala. Deep breathing activates the parasympathetic system and lowers cortisol in under 60 seconds.</div></div>
  </div>
</div>

<div class="modal-bg" id="crisis-modal">
  <div class="modal">
    <div style="font-size:40px">💙</div>
    <h2>We're here for you</h2>
    <p>You're not alone. Please reach out to one of these helplines — they are confidential and free.</p>
    <div class="helpline">iCall (Mon–Sat, 8am–10pm)<strong>9152987821</strong></div>
    <div class="helpline">NIMHANS Helpline<strong>080-46110007</strong></div>
    <div class="helpline">Vandrevala Foundation (24/7)<strong>1860-2662-345</strong></div>
    <button class="mc" onclick="closeCrisis()">I'll reach out — thank you</button>
  </div>
</div>

<script>
const CONDITIONS = CONDITIONS_JS_PLACEHOLDER;
let history=[],lang='en',mood='',apiKey='',recording=false,speechRec=null,activeCond=null;

function saveKey(){
  const v=document.getElementById('api-key-input').value.trim();
  if(v.length>15){apiKey=v;hideBanner();const b=document.getElementById('ai-badge');b.textContent='● Gemini Live';b.className='ai-badge live';}
  else alert('Please enter a valid Google AI key. Get one free at aistudio.google.com');
}
function skipKey(){hideBanner();}
function hideBanner(){
  document.getElementById('api-banner').style.display='none';
  document.querySelector('.app').style.paddingTop='52px';
}
function setLang(l,btn){lang=l;document.querySelectorAll('#lang-pill button').forEach(b=>b.classList.remove('on'));btn.classList.add('on');}
function setMode(m){
  ['chat','cond','doc'].forEach(id=>{const el=document.getElementById('btn-'+id);if(el)el.classList.remove('on');});
  const btn=document.getElementById('btn-'+m); if(btn)btn.classList.add('on');
  document.getElementById('chat-view').style.display=m==='chat'?'flex':'none';
  document.getElementById('conds-view').style.display=m==='conditions'?'block':'none';
  document.getElementById('doc-view').classList.toggle('show',m==='doctor');
  if(m==='conditions')buildEnc();
}
function switchTab(tab,btn){
  document.querySelectorAll('.stab').forEach(b=>b.classList.remove('on'));btn.classList.add('on');
  ['mood','history','conds'].forEach(t=>document.getElementById('tab-'+t).style.display=t===tab?'block':'none');
}
function selectCond(key){
  activeCond=key;
  document.querySelectorAll('.cond-card').forEach(c=>c.classList.toggle('active',c.dataset.key===key));
  updateAC(key);
  setMode('chat');document.getElementById('btn-chat').classList.add('on');
  const c=CONDITIONS[key];
  if(c)qs(`I think I might be dealing with ${c.name}. Can you help me understand and manage it?`);
}
function updateAC(key){
  const p=document.getElementById('ac-panel');
  if(!key||!CONDITIONS[key]){p.innerHTML='<div class="ac-hdr"><span class="ac-icon">🧠</span><span class="ac-name">General Support</span></div><div class="txt-sm">Start chatting — condition detected automatically.</div>';return;}
  const c=CONDITIONS[key];
  const syms=c.symptoms.map(s=>`<li>${s}</li>`).join('');
  const techs=c.techniques.map(t=>`<span class="ac-tech">${t}</span>`).join('');
  p.innerHTML=`<div class="ac-hdr"><span class="ac-icon">${c.icon}</span><span class="ac-name">${c.name}</span><span class="ac-badge">${c.phq_scale}</span></div><ul class="ac-syms">${syms}</ul><div class="ac-techs">${techs}</div>`;
}
function buildEnc(){
  const g=document.getElementById('enc-grid');
  if(g.children.length>0)return;
  Object.entries(CONDITIONS).forEach(([key,c])=>{
    const d=document.createElement('div');d.className='enc-card';
    d.innerHTML=`<div class="enc-icon">${c.icon}</div><div class="enc-name">${c.name}</div><div class="enc-desc">${c.description}</div><span class="enc-tag">${c.phq_scale}</span>`;
    d.onclick=()=>selectCond(key);g.appendChild(d);
  });
}
function pickMood(btn,emoji,label){
  document.querySelectorAll('.mb').forEach(b=>b.classList.remove('on'));btn.classList.add('on');mood=label;
  document.getElementById('mood-lbl').textContent='Feeling: '+emoji+' '+label;
}
function qs(t){document.getElementById('inp').value=t;sendMsg();}
function toggleChip(el){el.classList.toggle('on');}
function phqS(el){
  el.parentElement.querySelectorAll('.ps').forEach(s=>s.classList.remove('on'));el.classList.add('on');
  let t=0;document.querySelectorAll('.ps.on').forEach(s=>t+=parseInt(s.textContent));
  const v=document.getElementById('phq-t');v.textContent=t;v.style.color=t<=4?'var(--green)':t<=9?'var(--amber)':'var(--coral)';
}
function rsz(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,100)+'px';}
function onKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg();}}
function toggleMic(){
  const btn=document.getElementById('mic-btn');recording=!recording;
  btn.classList.toggle('rec',recording);btn.textContent=recording?'⏹️':'🎙️';
  if(recording){
    const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(SR){
      speechRec=new SR();speechRec.lang=lang==='hi'?'hi-IN':lang==='mr'?'mr-IN':lang==='ta'?'ta-IN':'en-IN';
      speechRec.onresult=e=>{document.getElementById('inp').value=e.results[0][0].transcript;if(recording)toggleMic();};
      speechRec.onerror=()=>{if(recording){toggleMic();demoVoice();}};speechRec.start();
    }else{setTimeout(()=>{if(recording){toggleMic();demoVoice();}},2200);}
  }else{if(speechRec){try{speechRec.stop();}catch(e){}speechRec=null;}}
}
function demoVoice(){const s=["I have been feeling really anxious lately","I feel low and hopeless about everything","I keep having intrusive thoughts I cannot stop","Work stress and burnout are overwhelming me","I cannot sleep no matter what I try"];document.getElementById('inp').value=s[Math.floor(Math.random()*s.length)];}
async function sendMsg(){
  const el=document.getElementById('inp'),text=el.value.trim();if(!text)return;
  const w=document.getElementById('welcome');if(w)w.remove();
  addMsg('u',text);el.value='';el.style.height='auto';
  history.push({role:'user',content:text});animScores();
  document.getElementById('typing').classList.add('show');scrollBot();
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,history:history.slice(-12),language:lang,mood,api_key:apiKey,condition_hint:activeCond||''})});
    const d=await r.json();
    document.getElementById('typing').classList.remove('show');
    addMsg('a',d.reply,d.biomarkers?.emotion,d.biomarkers?.condition);
    if(d.biomarkers)updateBio(d.biomarkers);if(d.crisis)showCrisis();
    history.push({role:'assistant',content:d.reply});
  }catch(e){document.getElementById('typing').classList.remove('show');addMsg('a','Connection issue — please try again.');}
  scrollBot();
}
function addMsg(role,text,emotion,condition){
  const msgs=document.getElementById('msgs'),div=document.createElement('div');div.className='msg '+role;
  const badge=(role==='a'&&emotion)?`<div class="e-badge"><span class="e-dot"></span>Detected: ${emotion}</div>`:'';
  let cb='';
  if(role==='a'&&condition&&condition!=='general'&&CONDITIONS[condition]){
    const c=CONDITIONS[condition];cb=`<div class="cond-banner"><span>${c.icon}</span>${c.name} identified</div>`;
    if(activeCond!==condition){activeCond=condition;updateAC(condition);document.querySelectorAll('.cond-card').forEach(cc=>cc.classList.toggle('active',cc.dataset.key===condition));}
  }
  const t=new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'});
  div.innerHTML=`${cb}${badge}<div class="bubble">${text.replace(/\n/g,'<br>')}</div><div class="msg-time">${t}</div>`;
  msgs.appendChild(div);scrollBot();
}
function scrollBot(){const m=document.getElementById('msgs');if(m)m.scrollTop=m.scrollHeight;}
function updateBio(b){
  const s=parseFloat(b.stress)||3;
  const el=document.getElementById('bm-s');el.textContent=s.toFixed(1);el.style.color=s>6.5?'var(--coral)':s>4.5?'var(--amber)':'var(--green)';
  document.getElementById('bm-sd').textContent=s>6.5?'High distress':s>4.5?'Moderate tension':'Low stress';
  if(b.energy!==undefined)document.getElementById('bm-e').textContent=parseFloat(b.energy).toFixed(2);
  if(b.pace)document.getElementById('bm-p').textContent=Math.round(b.pace);
  if(b.insight)document.getElementById('insight-txt').textContent=b.insight;
  if(b.psycho)document.getElementById('psycho-txt').textContent=b.psycho;
  const box=document.getElementById('status-box');
  if(s>7.5){box.className='status-box s-crisis';box.textContent='⚠️ High distress. Clinical check-in recommended.';}
  else if(s>5){box.className='status-box s-warn';box.textContent='🔶 Elevated stress signals.';}
  else{box.className='status-box s-calm';box.textContent='✅ All signals normal.';}
}
function animScores(){
  const cl=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
  let a=parseFloat(document.getElementById('anx-v').textContent);
  let mo=parseFloat(document.getElementById('mood-v').textContent);
  let st=parseFloat(document.getElementById('stress-v').textContent);
  a=cl(a+(Math.random()>.55?.3:-.2),1,9.5);mo=cl(mo+(Math.random()>.45?.2:-.15),1,9.5);st=cl(st+(Math.random()>.5?.25:-.2),1,9.5);
  document.getElementById('anx-v').textContent=a.toFixed(1);document.getElementById('mood-v').textContent=mo.toFixed(1);document.getElementById('stress-v').textContent=st.toFixed(1);
  document.getElementById('anx-b').style.width=(a/10*100)+'%';document.getElementById('mood-b').style.width=(mo/10*100)+'%';document.getElementById('stress-b').style.width=(st/10*100)+'%';
}
function loadHist(key){
  const map={'30May':[{r:'u',t:'Work stress is making me very anxious'},{r:'a',t:"It sounds like work has been completely overwhelming your system. In India, work pressure often carries extra weight — the pressure to perform and provide. What's been the most draining part for you?",e:'anxious',c:'anxiety'}],'28May':[{r:'u',t:'I had a good weekend and feel more rested'},{r:'a',t:"That's genuinely good to hear — and worth pausing to notice, because it tells you what you need exists. What helped you recharge?",e:'hopeful',c:'general'}],'25May':[{r:'u',t:'Exam results tomorrow and I am so anxious'},{r:'a',t:"Exam anxiety is universal — your nervous system is preparing for uncertainty. Whatever the result, it doesn't define your worth. What's the outcome you're most afraid of?",e:'anxious',c:'anxiety'}],'22May':[{r:'u',t:'My OCD thoughts are really bad today'},{r:'a',t:"Those intrusive thoughts are so exhausting — and I want you to know they don't reflect who you are. OCD generates thoughts precisely because they're the most distressing. The goal is to not give them authority. What's showing up today?",e:'anxious',c:'ocd'}],'18May':[{r:'u',t:'No motivation, everything feels flat and grey'},{r:'a',t:"That flatness is one of the most characteristic experiences of depression — not laziness, but a real shift in how the brain processes reward and meaning. Has this been building gradually?",e:'sad',c:'depression'}]};
  const w=document.getElementById('welcome');if(w)w.remove();
  const msgs=document.getElementById('msgs');msgs.innerHTML='';
  (map[key]||[]).forEach(m=>addMsg(m.r,m.t,m.e,m.c));
  history=(map[key]||[]).map(m=>({role:m.r==='a'?'assistant':'user',content:m.t}));
  setMode('chat');document.getElementById('btn-chat').classList.add('on');
}
function showCrisis(){document.getElementById('crisis-modal').classList.add('show');}
function closeCrisis(){document.getElementById('crisis-modal').classList.remove('show');}
document.querySelector('.app').style.paddingTop='94px';
</script>
</body>
</html>"""

# Inject dynamic parts
HTML_FINAL = HTML.replace("CONDITION_CARDS_PLACEHOLDER", _cond_cards()).replace("CONDITIONS_JS_PLACEHOLDER", CONDITIONS_JS)


# ─────────────────────────────────────────────────────────────────
#  ROUTER
# ─────────────────────────────────────────────────────────────────

def route(method, path, body):
    h = cors()
    if method=="GET" and path in ("/",""):
        return HTML_FINAL,200,{**h,"Content-Type":"text/html; charset=utf-8"}
    if method=="OPTIONS": return "",204,h
    if method=="POST" and path=="/api/chat":
        msg=body.get("message","").strip()
        if not msg: return json_resp({"error":"message required"},400)
        result=gemini_chat(msg,body.get("history",[]),body.get("language","en"),body.get("mood",""),body.get("condition_hint",""),body.get("api_key",""))
        return json_resp({"reply":result.get("reply",""),"biomarkers":result.get("biomarkers",{}),"crisis":result.get("crisis",False)})
    if method=="POST" and path=="/api/mood":
        e={"id":new_id(),"user_id":body.get("user_id","anon"),"emoji":body.get("emoji","😐"),"label":body.get("label","Neutral"),"anxiety":float(body.get("anxiety",5)),"mood":float(body.get("mood",5)),"stress":float(body.get("stress",5)),"logged_at":datetime.utcnow().isoformat()}
        MOOD_LOGS.append(e);return json_resp({"ok":True,"entry":e})
    if method=="GET" and path.startswith("/api/mood/trend"):
        dates,anx,mv,sv=[],[],[],[]
        for i in range(14,0,-1):
            d=datetime.utcnow()-timedelta(days=i);dates.append(d.strftime("%b %d"))
            anx.append(round(random.uniform(2,7),1));mv.append(round(random.uniform(4,9),1));sv.append(round(random.uniform(2,6),1))
        return json_resp({"dates":dates,"anxiety":anx,"mood":mv,"stress":sv})
    if method=="POST" and path=="/api/auth/send-otp":
        phone=body.get("phone","")
        if not phone: return json_resp({"error":"phone required"},400)
        otp="".join(str(random.randint(0,9)) for _ in range(6))
        OTP_STORE[phone]={"otp":otp,"expires":now_ts()+600}
        print(f"[OTP] {phone} → {otp}");return json_resp({"ok":True,"message":"OTP sent"})
    if method=="POST" and path=="/api/auth/verify-otp":
        phone=body.get("phone","");otp=body.get("otp","");rec=OTP_STORE.get(phone)
        if not rec: return json_resp({"error":"No OTP found"},404)
        if now_ts()>rec["expires"]: return json_resp({"error":"OTP expired"},410)
        if rec["otp"]!=otp: return json_resp({"error":"Wrong OTP"},401)
        del OTP_STORE[phone];uid=f"user_{phone[-4:]}"
        return json_resp({"ok":True,"token":make_jwt(uid),"user_id":uid})
    if method=="POST" and path=="/api/summary":
        return json_resp({"summary":gemini_summary(body.get("messages",[]),body.get("api_key",""))})
    if method=="POST" and path=="/api/alert":
        e={"id":new_id(),"user_id":body.get("user_id","anon"),"level":body.get("level","medium"),"trigger":body.get("trigger","manual"),"at":datetime.utcnow().isoformat()}
        ALERT_LOG.append(e);print(f"[ALERT][{e['level'].upper()}] {e}");return json_resp({"ok":True,"alert_id":e["id"]})
    if method=="GET" and path=="/api/conditions":
        return json_resp({"conditions":{k:{"name":v["name"],"icon":v["icon"],"description":v["description"],"symptoms":v["symptoms"],"techniques":v["techniques"],"phq_scale":v["phq_scale"]} for k,v in PSYCH_CONDITIONS.items()}})
    if method=="GET" and path=="/api/health":
        return json_resp({"status":"ok","service":"MindWell v2.0","ai_ready":bool(GOOGLE_API_KEY),"conditions":len(PSYCH_CONDITIONS),"moods":len(MOOD_LOGS),"alerts":len(ALERT_LOG)})
    return json_resp({"error":"Not found"},404)


# ─────────────────────────────────────────────────────────────────
#  VERCEL HANDLER  (WSGI-compatible — works with @vercel/python)
# ─────────────────────────────────────────────────────────────────

def app(environ, start_response):
    """WSGI entry point — Vercel calls this automatically."""
    method = environ.get("REQUEST_METHOD", "GET")
    path   = environ.get("PATH_INFO", "/")

    # Parse body for POST/PUT
    body = {}
    if method in ("POST", "PUT", "PATCH"):
        try:
            length = int(environ.get("CONTENT_LENGTH", 0) or 0)
            raw    = environ["wsgi.input"].read(length)
            body   = json.loads(raw) if raw else {}
        except Exception:
            body = {}

    resp_body, status_code, headers = route(method, path, body)

    status_str = f"{status_code} OK" if status_code == 200 else str(status_code)
    header_list = [(k, v) for k, v in headers.items()]
    start_response(status_str, header_list)

    if isinstance(resp_body, str):
        resp_body = resp_body.encode()
    return [resp_body]


# Vercel looks for a symbol named `handler` — point it at the WSGI app
handler = app


# ─────────────────────────────────────────────────────────────────
#  LOCAL DEV
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    key_status = "SET ✅" if GOOGLE_API_KEY else "NOT SET — demo mode ⚠️"
    print(f"""
╔══════════════════════════════════════════════════════════╗
║         MindWell v2.0 — Mental Health AI Platform        ║
╠══════════════════════════════════════════════════════════╣
║  URL        →  http://localhost:{PORT}                     ║
║  AI         →  Google Gemini 1.5 Flash                   ║
║  API Key    →  {key_status}                      ║
║  Conditions →  {len(PSYCH_CONDITIONS)} psychological conditions            ║
╠══════════════════════════════════════════════════════════╣
║  Routes:                                                 ║
║  GET  /                     Frontend                     ║
║  POST /api/chat             AI conversation              ║
║  GET  /api/conditions       All conditions               ║
║  POST /api/mood             Log mood                     ║
║  GET  /api/mood/trend       14-day trend                 ║
║  POST /api/auth/send-otp    OTP auth                     ║
║  POST /api/auth/verify-otp  Verify OTP + JWT             ║
║  POST /api/summary          Session summary              ║
║  POST /api/alert            Crisis alert                 ║
║  GET  /api/health           Health check                 ║
╚══════════════════════════════════════════════════════════╝
""")
    HTTPServer(("", PORT), handler).serve_forever()
