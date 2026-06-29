"""
MindWell v4.0 — Mental Health AI Platform
==========================================
- NO API key prompt for users — key is server-side only
- Fully working onboarding (role selection only)
- Google Gemini AI — auto-connects from environment
- All 16 conditions, doctor dashboard, crisis modal
- Voice input, mood tracking, session history
- Vercel WSGI ready
"""

import json, os, re, uuid, hmac, hashlib, base64, time, random
from datetime import datetime, timedelta

# ─── CONFIG ───────────────────────────────────────────────────────
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
JWT_SECRET     = os.environ.get("JWT_SECRET", "mindwell-2026")

# ─── DATA ─────────────────────────────────────────────────────────
MOOD_LOGS, ALERT_LOG, OTP_STORE = [], [], {}

CRISIS_KEYWORDS = [
    "want to die","kill myself","end my life","suicidal","self harm",
    "hurt myself","no reason to live","better off dead","take my life",
    "end it all","not worth living","want to disappear","cut myself",
    "overdose","jump off","मरना चाहता","जिंदगी खत्म","खुद को नुकसान",
]

PSYCH_CONDITIONS = {
    "anxiety":        {"name":"Anxiety Disorder","icon":"😰","color":"#f0b429","description":"Persistent worry, restlessness and physical tension affecting daily life","symptoms":["Excessive worry","Restlessness","Fatigue","Difficulty concentrating","Muscle tension","Sleep disturbance","Irritability"],"techniques":["4-7-8 Breathing","5-4-3-2-1 Grounding","Progressive Muscle Relaxation","Worry Journaling","Cognitive Restructuring"],"phq_scale":"GAD-7","triggers":["work","exam","future","worry","nervous","panic","fear","anxious","overwhelm","dread","scared"]},
    "depression":     {"name":"Major Depression","icon":"😔","color":"#6366f1","description":"Persistent low mood, loss of interest and fatigue affecting daily functioning","symptoms":["Persistent sadness","Loss of interest","Fatigue","Sleep changes","Appetite changes","Worthlessness","Difficulty concentrating"],"techniques":["Behavioural Activation","Thought Records","Self-Compassion","Gratitude Journaling","Social Engagement Plan"],"phq_scale":"PHQ-9","triggers":["sad","hopeless","empty","worthless","numb","depressed","no motivation","nothing matters","low","miserable"]},
    "ocd":            {"name":"OCD","icon":"🔄","color":"#8b5cf6","description":"Intrusive thoughts and repetitive compulsions causing significant distress","symptoms":["Intrusive thoughts","Repetitive behaviours","Fear of contamination","Need for symmetry","Checking rituals","Mental counting"],"techniques":["ERP (Exposure Response Prevention)","Thought Defusion","Mindfulness","Delay and Redirect","ACT Acceptance"],"phq_scale":"OCI-R","triggers":["obsession","compulsion","checking","contamination","intrusive","rituals","symmetry","repeating","can't stop"]},
    "ptsd":           {"name":"PTSD","icon":"⚡","color":"#ef4444","description":"Re-experiencing trauma, hypervigilance and avoidance after a traumatic event","symptoms":["Flashbacks","Nightmares","Hypervigilance","Avoidance","Emotional numbness","Startle response","Memory gaps"],"techniques":["Grounding Techniques","Safe Place Visualisation","Trauma-Focused CBT","Bilateral Stimulation","EMDR with therapist"],"phq_scale":"PCL-5","triggers":["trauma","flashback","nightmare","abuse","accident","assault","triggered","hypervigilant","numb","avoid"]},
    "bipolar":        {"name":"Bipolar Disorder","icon":"🌊","color":"#0ea5e9","description":"Episodes of mania or hypomania alternating with depressive episodes","symptoms":["Elevated mood","Racing thoughts","Decreased sleep need","Impulsivity","Grandiosity","Irritability","Depressive episodes"],"techniques":["Mood Charting","Sleep Regularity","Medication Adherence","Early Warning Signs","Routine Structuring"],"phq_scale":"MDQ","triggers":["manic","hypomania","mood swings","racing thoughts","don't need sleep","grandiose","impulsive","episode"]},
    "panic":          {"name":"Panic Disorder","icon":"💨","color":"#f97316","description":"Recurrent unexpected panic attacks with persistent fear of future attacks","symptoms":["Racing heart","Shortness of breath","Chest pain","Dizziness","Sweating","Fear of dying","Trembling"],"techniques":["Diaphragmatic Breathing","DARE Response","Interoceptive Exposure","Controlled Breathing","Panic Diary"],"phq_scale":"PDSS","triggers":["panic attack","heart racing","can't breathe","chest pain","dizzy","fear of dying","palpitations","shaking"]},
    "social_anxiety": {"name":"Social Anxiety","icon":"👥","color":"#10b981","description":"Intense fear of social situations, judgement and embarrassment","symptoms":["Fear of judgement","Blushing","Sweating in crowds","Avoiding gatherings","Fear of speaking","Self-consciousness"],"techniques":["Social Exposure Hierarchy","Cognitive Restructuring","Role Play Practice","Mindfulness in Social","Video Feedback"],"phq_scale":"SPIN","triggers":["social","judged","embarrass","awkward","people","presentation","crowd","party","speaking","shy"]},
    "eating_disorder":{"name":"Eating Disorder","icon":"🍽️","color":"#ec4899","description":"Distorted relationship with food and body — Anorexia, Bulimia or BED","symptoms":["Distorted body image","Restrictive eating","Binge eating","Purging","Food preoccupation","Weight obsession"],"techniques":["Mindful Eating","Body Image Work","Meal Planning Support","Challenging Food Rules","Self-Compassion"],"phq_scale":"EDE-Q","triggers":["eating","food","weight","fat","body","binge","purge","restrict","calories","diet","anorexia","bulimia"]},
    "adhd":           {"name":"ADHD","icon":"🎯","color":"#f59e0b","description":"Attention deficit, impulsivity and hyperactivity affecting daily functioning","symptoms":["Difficulty focusing","Forgetfulness","Impulsivity","Hyperactivity","Disorganisation","Time blindness","Emotional dysregulation"],"techniques":["Pomodoro Technique","Body Doubling","External Reminders","Dopamine Scheduling","Task Chunking"],"phq_scale":"ASRS","triggers":["can't focus","distracted","forget","impulsive","hyper","adhd","scattered","procrastinate","disorganised"]},
    "grief":          {"name":"Grief and Loss","icon":"🕊️","color":"#64748b","description":"Processing loss of a loved one, relationship or significant life change","symptoms":["Intense sadness","Yearning","Disbelief","Anger","Guilt","Social withdrawal","Physical pain"],"techniques":["Grief Journaling","Continuing Bonds","Meaning Making","Ritual and Remembrance","Support Groups"],"phq_scale":"PG-13","triggers":["loss","death","died","passed away","grief","bereaved","miss them","gone","mourning","funeral"]},
    "burnout":        {"name":"Burnout","icon":"🔥","color":"#dc2626","description":"Chronic workplace stress causing exhaustion, cynicism and reduced efficacy","symptoms":["Exhaustion","Cynicism","Reduced performance","Detachment","Physical symptoms","Reduced motivation"],"techniques":["Boundary Setting","Work-Life Audit","Recovery Planning","Values Clarification","Rest Scheduling"],"phq_scale":"MBI","triggers":["burnout","work","exhausted","no energy","hate job","overworked","no boundaries","used up","done","quit"]},
    "sleep":          {"name":"Sleep Disorder","icon":"😴","color":"#1d4ed8","description":"Insomnia, hypersomnia or disrupted sleep patterns affecting daily life","symptoms":["Difficulty falling asleep","Early waking","Non-restorative sleep","Daytime fatigue","Mood irritability","Difficulty concentrating"],"techniques":["Sleep Restriction Therapy","Stimulus Control","Sleep Hygiene","CBT-I Protocol","Screen Curfew"],"phq_scale":"ISI","triggers":["can't sleep","insomnia","awake","tired","exhausted","nightmare","sleep","rest","fatigue","3am"]},
    "addiction":      {"name":"Addiction","icon":"🔗","color":"#7c3aed","description":"Compulsive substance use or behavioural addiction despite harmful consequences","symptoms":["Craving","Loss of control","Withdrawal","Tolerance","Neglecting responsibilities","Continued use despite consequences"],"techniques":["HALT Check","Urge Surfing","Trigger Mapping","Support Network","Relapse Prevention Plan"],"phq_scale":"AUDIT","triggers":["addiction","alcohol","drugs","smoking","gambling","craving","can't stop","relapse","dependent","withdrawal"]},
    "bpd":            {"name":"Borderline Personality","icon":"🌪️","color":"#be185d","description":"Emotional dysregulation, unstable relationships and identity disturbance","symptoms":["Fear of abandonment","Unstable relationships","Identity disturbance","Impulsivity","Emotional lability","Self-harm","Dissociation"],"techniques":["DBT TIPP Skill","Opposite Action","DEAR MAN Communication","Mindfulness","Radical Acceptance"],"phq_scale":"ZAN-BPD","triggers":["abandoned","borderline","unstable","emptiness","self harm","cutting","impulsive","identity","splitting","intense"]},
    "schizophrenia":  {"name":"Psychosis / Schizophrenia","icon":"🌀","color":"#0891b2","description":"Disrupted thinking, perception, emotions and behaviour","symptoms":["Hallucinations","Delusions","Disorganised thinking","Flat affect","Social withdrawal","Cognitive difficulties"],"techniques":["Reality Testing","Medication Adherence","Structured Routine","Social Skills Training","Stress Reduction"],"phq_scale":"PANSS","triggers":["voices","hearing things","seeing things","paranoid","delusion","not real","losing mind","psychosis","episode"]},
    "phobia":         {"name":"Specific Phobia","icon":"😱","color":"#059669","description":"Intense irrational fear of specific objects, situations or activities","symptoms":["Intense fear","Avoidance","Panic on exposure","Anticipatory anxiety","Physical symptoms","Recognising fear as excessive"],"techniques":["Graduated Exposure","Systematic Desensitisation","Virtual Reality Exposure","Relaxation During Exposure","Fear Hierarchy"],"phq_scale":"SPS","triggers":["phobia","scared of","fear of","terrified","can't go near","avoid","spider","height","blood","flying","needle"]},
}

PSYCHO_FACTS = [
    "Anxiety activates the amygdala. The 4-7-8 breath physiologically reverses cortisol response in 60 seconds.",
    "Low mood depletes dopamine. Even a 10-minute walk increases dopamine by up to 30%.",
    "Sleep deprivation raises cortisol by 37%. A consistent wake time resets your circadian rhythm in 7 days.",
    "The 5-4-3-2-1 grounding technique interrupts anxious thought loops by engaging all 5 senses.",
    "Writing worries down offloads cognitive load from the prefrontal cortex — science-backed clarity.",
    "Loneliness activates the same brain region as physical pain. Connection is a biological need.",
    "Gratitude journaling 3 items daily rewires the brain's negativity bias within 3 weeks.",
    "Box breathing (4-4-4-4) is used by Navy SEALs to calm the nervous system under pressure.",
    "Naming an emotion reduces amygdala activation — labelling the feeling defuses its power.",
    "Exercise is as effective as antidepressants for mild-moderate depression in controlled studies.",
    "Cold water on the face activates the diving reflex — heart rate drops within 30 seconds.",
    "The vagus nerve connects gut to brain. Slow exhales activate it, triggering the calm response.",
]

LANGUAGE_MAP = {
    "en": "Respond in English.",
    "hi": "Respond in Hindi (Devanagari). Warm, familiar tone using 'aap'.",
    "mr": "Respond in Marathi (Devanagari). Culturally sensitive to Maharashtra.",
    "ta": "Respond in Tamil script. Warm and empathetic.",
}

GEMINI_SYSTEM = """You are MindWell, an expert compassionate mental health AI for India.

CLINICAL EXPERTISE:
Anxiety (GAD, panic, social, phobias), Depression, OCD, PTSD, Bipolar Disorder,
Schizophrenia/Psychosis, Eating Disorders, ADHD, Addiction, BPD, Grief, Burnout,
Sleep Disorders, Dissociation, Self-harm, Suicidal ideation.

APPROACH:
- Validate first. Always acknowledge the person's experience before anything else.
- Ask ONE focused follow-up question per response.
- Keep responses warm, concise (3-5 sentences), conversational.
- Use Indian cultural context naturally (family pressure, career expectations).
- First message: warmly acknowledge, ask about context, do not jump to techniques yet.
- Subsequent messages: go deeper, offer one specific technique when appropriate.

SAFETY (absolute):
- Suicidal ideation → deep care + iCall: 9152987821, NIMHANS: 080-46110007, Vandrevala: 1860-2662-345
- Active psychosis → recommend immediate clinical help
- Self-harm → set crisis:true, provide resources
- Never formally diagnose. Always recommend professional evaluation.

RESPONSE FORMAT:
- 3-5 warm, natural sentences maximum
- One thoughtful follow-up question OR one specific brief exercise
- Never start with "I"

BIOMARKER JSON — always on its own line at the very end (no markdown, no backticks):
{"stress":0-10,"energy":0.0-1.0,"pace":wpm_int,"emotion":"label","condition":"key","insight":"clinical_note","psycho":"fact","crisis":false}
Emotion: neutral/happy/sad/anxious/angry/fearful/overwhelmed/hopeful/tired/lonely
Condition keys: anxiety/depression/ocd/ptsd/bipolar/panic/social_anxiety/eating_disorder/adhd/grief/burnout/sleep/addiction/bpd/schizophrenia/phobia/general"""

# ─── UTILITIES ────────────────────────────────────────────────────
def new_id():  return str(uuid.uuid4())[:8]
def now_ts():  return int(time.time())

def detect_crisis(text):
    t = text.lower()
    return any(k in t for k in CRISIS_KEYWORDS)

def detect_condition(text):
    """Longest-match wins — prevents 'panic' in anxiety triggers beating 'panic attack'."""
    t = text.lower()
    best_key = "general"
    best_len = 0
    for key, c in PSYCH_CONDITIONS.items():
        for tr in c["triggers"]:
            if tr in t and len(tr) > best_len:
                best_key = key
                best_len = len(tr)
    return best_key

def parse_bio(raw):
    default = {
        "stress": 3.0, "energy": 0.6, "pace": 130,
        "emotion": "neutral", "condition": "general",
        "insight": "Session in progress.",
        "psycho": PSYCHO_FACTS[now_ts() % len(PSYCHO_FACTS)],
        "crisis": False
    }
    m = re.search(r'\{[^\{\}]+\}', raw, re.DOTALL)
    if not m:
        return raw.strip(), default
    try:
        data  = json.loads(m.group())
        clean = raw[:m.start()].strip()
        return clean, {**default, **data}
    except Exception:
        return raw.strip(), default

def cors():
    return {
        "Access-Control-Allow-Origin":  "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
    }

def json_resp(data, status=200):
    return json.dumps(data), status, {"Content-Type": "application/json"}

# ─── GEMINI AI ────────────────────────────────────────────────────
def gemini_chat(message, history, language="en", mood="", condition_hint="", user_type="patient"):
    key = GOOGLE_API_KEY
    if not key:
        return _demo(message)
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        cctx = ""
        if condition_hint and condition_hint in PSYCH_CONDITIONS:
            c = PSYCH_CONDITIONS[condition_hint]
            cctx = (f"\n\nACTIVE CONDITION: {c['name']}. "
                    f"Symptoms: {', '.join(c['symptoms'][:4])}. "
                    f"Techniques: {', '.join(c['techniques'][:3])}.")
        doc_ctx = "\n\nSpeaking with DOCTOR/CLINICIAN. Use clinical language, mention PHQ-9/GAD-7, discuss treatment planning." if user_type == "doctor" else ""
        system = GEMINI_SYSTEM + f"\n\n{LANGUAGE_MAP.get(language, '')}" + cctx + doc_ctx
        if detect_crisis(message):
            system += "\n\nCRITICAL: Crisis signals. Respond with deep empathy, provide all three helplines, set crisis:true."
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=system)
        ghist = [{"role": "user" if h["role"] == "user" else "model", "parts": [h["content"]]} for h in history[-10:]]
        chat  = model.start_chat(history=ghist)
        prefix = f"[Mood: {mood}] " if mood else ""
        resp = chat.send_message(prefix + message)
        clean, bio = parse_bio(resp.text)
        if bio.get("condition", "general") == "general":
            d = detect_condition(message)
            if d != "general": bio["condition"] = d
        return {"reply": clean, "biomarkers": bio, "crisis": detect_crisis(message) or bool(bio.get("crisis"))}
    except ImportError:
        return {"reply": "Server setup issue: google-generativeai not installed.", "biomarkers": {}, "crisis": False}
    except Exception as e:
        err = str(e)
        if "quota" in err.lower() or "429" in err:
            return {"reply": "I'm getting a lot of requests right now. Please try again in a moment.", "biomarkers": {}, "crisis": False}
        return _demo(message)

def gemini_summary(messages):
    key = GOOGLE_API_KEY
    if not key or not messages:
        return "No API key configured on server. Add GOOGLE_API_KEY to Vercel environment variables."
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        conv  = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in messages[-20:])
        resp  = model.generate_content(
            "Summarise this mental health session for the treating psychiatrist.\n"
            "Sections: 1.Chief Complaint  2.Emotional Trajectory  3.Possible Condition(s)  4.Risk Level  5.Recommended Actions\n"
            "Clinical, concise. Max 200 words.\n\nCONVERSATION:\n" + conv
        )
        return resp.text
    except Exception as e:
        return f"Summary error: {str(e)[:100]}"

# ─── DEMO FALLBACK ────────────────────────────────────────────────
def _demo(text):
    t = text.lower()
    cond = detect_condition(t)
    demos = {
        "anxiety":        ("That anxious feeling can be so consuming — like your thoughts are racing faster than you can catch them. What you're experiencing makes complete sense, and it's your nervous system trying to protect you. Try this right now: breathe in for 4 counts, hold for 7, out for 8 — it activates your parasympathetic system in under a minute. What do you think is the root of this anxiety?",         {"stress":6.5,"energy":0.78,"pace":158,"emotion":"anxious","condition":"anxiety","insight":"GAD presentation. 4-7-8 breathing recommended. Explore triggers.","psycho":"Anxiety activates the amygdala. The 4-7-8 breath reverses cortisol response in under 60 seconds.","crisis":False}),
        "depression":     ("Feeling that weight is one of the hardest things to carry — and yet here you are, reaching out, which takes real courage. You don't have to make sense of everything right now. Has this heaviness been building for a while, or did something specific change recently?",                                                                                                                                   {"stress":5.2,"energy":0.38,"pace":112,"emotion":"sad","condition":"depression","insight":"Low mood, reduced energy. PHQ-9 screening recommended.","psycho":"Low mood depletes dopamine. Even 10 minutes of physical movement increases dopamine by up to 30%.","crisis":False}),
        "ocd":            ("Those intrusive thoughts are exhausting to live with — and the thought itself doesn't reflect who you are. OCD hijacks your threat-detection system. The key insight is to notice the urge without acting on it, even for 5 minutes. What kind of thoughts feel most overwhelming right now?",                                                                                                           {"stress":6.8,"energy":0.65,"pace":145,"emotion":"anxious","condition":"ocd","insight":"OCD intrusive thought presentation. ERP psychoeducation appropriate. Avoid reassurance.","psycho":"OCD is maintained by rituals. ERP — facing anxiety without the ritual — breaks this cycle with 60-80% effectiveness.","crisis":False}),
        "ptsd":           ("Thank you for trusting me with this. You don't need to share any details you're not ready for — we can go at whatever pace feels safe. Right now, can you feel your feet on the floor and name 3 things you can see around you? Let's get grounded first.",                                                                                                                                            {"stress":7.5,"energy":0.45,"pace":118,"emotion":"fearful","condition":"ptsd","insight":"Possible PTSD. Prioritise grounding and safety. Do not push for trauma narrative.","psycho":"Trauma activates the survival brain. Grounding techniques reconnect the prefrontal cortex, reducing flashback intensity.","crisis":False}),
        "bipolar":        ("What you're describing sounds like a real shift in your energy and mood — these changes are important to pay attention to. Tracking your sleep is one of the most powerful early warning signs for mood episodes. How has your sleep been over the last week?",                                                                                                                                          {"stress":5.5,"energy":0.88,"pace":175,"emotion":"overwhelmed","condition":"bipolar","insight":"Possible hypomanic features. Sleep monitoring critical. Check medication adherence.","psycho":"In Bipolar Disorder, sleep disruption is both a trigger and early warning sign of mood episodes.","crisis":False}),
        "panic":          ("A panic attack is terrifying in the moment — your body is flooded with signals that feel like danger even when you're physically safe. The most important thing to know: it will always pass. Try breathing out slowly — longer exhale than inhale. Did this come on suddenly or did you feel it building?",                                                                                              {"stress":8.2,"energy":0.92,"pace":182,"emotion":"fearful","condition":"panic","insight":"Panic attack presentation. Psychoeducation on panic cycle essential. Diaphragmatic breathing as immediate intervention.","psycho":"Panic attacks always peak within 10 minutes and pass. Your body knows how to recover.","crisis":False}),
        "social_anxiety": ("The fear of being judged makes every interaction feel like a high-stakes performance — that's genuinely exhausting to carry. What you feel makes sense, even if the fear is bigger than the actual risk most of the time. What social situation feels most overwhelming for you right now?",                                                                                                            {"stress":5.8,"energy":0.52,"pace":128,"emotion":"anxious","condition":"social_anxiety","insight":"Social Anxiety Disorder. Exposure hierarchy and cognitive restructuring indicated.","psycho":"Social anxiety involves overestimating how much others notice our mistakes. Research shows people focus on us far less than we believe.","crisis":False}),
        "eating_disorder":("The relationship with food and your body can be one of the most complex struggles — and you're not alone in it. It takes real courage to even speak about this. I want this to be a safe space with no judgement. What's been feeling most difficult lately?",                                                                                                                                        {"stress":6.0,"energy":0.42,"pace":120,"emotion":"sad","condition":"eating_disorder","insight":"Possible eating disorder. Body-neutral language essential. Refer to specialist service.","psycho":"Eating disorders have the highest mortality of any mental health condition. Recovery is absolutely possible with the right specialist support.","crisis":False}),
        "adhd":           ("That struggle to focus is real — and it's not laziness or a character flaw. The ADHD brain is wired differently, not broken. Try this: break the task into the tiniest possible first step. What's the one thing you're finding hardest to start right now?",                                                                                                                                        {"stress":5.0,"energy":0.75,"pace":168,"emotion":"overwhelmed","condition":"adhd","insight":"ADHD executive function difficulties. Task initiation and working memory challenges.","psycho":"ADHD involves dopamine dysregulation. External structure and novelty help activate the brain's focus system.","crisis":False}),
        "grief":          ("Grief is one of the most profound human experiences — there's no right way, no timeline, no finish line. What you feel is real and deserves space. Would you like to tell me a little about the person or thing you've lost, if you feel ready?",                                                                                                                                                     {"stress":5.5,"energy":0.35,"pace":108,"emotion":"sad","condition":"grief","insight":"Acute grief. No timeline pressure. Meaning-making approach when patient is ready.","psycho":"Grief doesn't disappear — it changes shape over time and integrates into who you become.","crisis":False}),
        "burnout":        ("What you're describing is burnout — and this is not weakness, it's what happens when a person gives more than their system can sustain for too long. When did you last feel like yourself, not just a function at work?",                                                                                                                                                                              {"stress":7.8,"energy":0.22,"pace":105,"emotion":"tired","condition":"burnout","insight":"Severe burnout. Immediate rest and boundary-setting critical. Systemic factors to explore.","psycho":"Burnout requires active recovery, not just absence from work. The nervous system needs deliberate repair.","crisis":False}),
        "sleep":          ("Sleep problems and emotional health are deeply connected — when one suffers, the other follows. The most evidence-based approach is CBT-I (Cognitive Behavioural Therapy for Insomnia), which is more effective long-term than sleep medication. Is it harder to fall asleep, stay asleep, or do you wake too early?",                                                                                 {"stress":4.5,"energy":0.28,"pace":118,"emotion":"tired","condition":"sleep","insight":"Insomnia presentation. CBT-I protocol recommended. Rule out sleep apnea.","psycho":"Sleep restriction therapy is counterintuitive but highly effective for rebuilding healthy sleep drive.","crisis":False}),
        "addiction":      ("It takes real honesty and courage to name this. Addiction isn't a moral failing — it's a brain condition where the reward system has been hijacked. Craving is not weakness. What does a typical day look like around this for you?",                                                                                                                                                                 {"stress":6.5,"energy":0.55,"pace":138,"emotion":"overwhelmed","condition":"addiction","insight":"Substance use presentation. Motivational interviewing approach. HALT check and trigger mapping recommended.","psycho":"Addiction creates physical changes in the prefrontal cortex. Recovery literally rebuilds these neural pathways over time.","crisis":False}),
        "bpd":            ("The intensity of what you feel is real — emotions that big are exhausting to carry. DBT was built specifically for this experience. The TIPP skill (Temperature, Intense exercise, Paced breathing, Progressive relaxation) can help when emotions feel unbearable. What's happening right now that's bringing this up?",                                                                               {"stress":7.2,"energy":0.82,"pace":165,"emotion":"overwhelmed","condition":"bpd","insight":"BPD features. DBT skills appropriate. Validate emotion without reinforcing crisis behaviour.","psycho":"DBT has strong evidence for BPD — 77% reduction in self-harm in clinical trials.","crisis":False}),
        "schizophrenia":  ("I hear you, and I'm right here with you. What you're experiencing sounds frightening and confusing, and I want to help you feel safe. The most important thing right now is your safety. Is there someone with you, or someone you can call to be with you?",                                                                                                                                        {"stress":8.0,"energy":0.50,"pace":125,"emotion":"fearful","condition":"schizophrenia","insight":"Possible psychotic symptoms. Urgent clinical referral. Do not challenge delusions. Safety assessment priority.","psycho":"Psychosis is a medical condition involving brain chemistry changes. With the right treatment, most people make significant recovery.","crisis":True}),
        "phobia":         ("Specific phobias are incredibly common — and the brain has learned to treat something as danger even when it isn't. The good news is that phobias respond very well to graduated exposure therapy. What happens in your body when you encounter or think about what you fear?",                                                                                                                        {"stress":6.0,"energy":0.68,"pace":148,"emotion":"fearful","condition":"phobia","insight":"Specific phobia. Graduated exposure hierarchy and fear thermometer appropriate.","psycho":"Phobias are maintained by avoidance. Gradual exposure breaks the cycle — each step makes the next one easier.","crisis":False}),
    }
    if cond in demos:
        reply, bio = demos[cond]
        return {"reply": reply, "biomarkers": bio, "crisis": bool(bio.get("crisis"))}
    # Crisis override — always provide helplines for crisis phrases
    if detect_crisis(t):
        return {
            "reply": ("You don't have to face this alone, and reaching out right now took real courage. "
                      "Please talk to someone who can truly be there for you:\n\n"
                      "📞 iCall: 9152987821 (Mon–Sat, 8am–10pm)\n"
                      "📞 NIMHANS: 080-46110007\n"
                      "📞 Vandrevala (24/7): 1860-2662-345\n\n"
                      "I'm here too — can you tell me a little about what's been building up for you?"),
            "biomarkers": {"stress": 9.0, "energy": 0.30, "pace": 100, "emotion": "fearful",
                           "condition": "general",
                           "insight": "Crisis signals detected. Helplines provided. Urgent clinical referral.",
                           "psycho": "Crisis support is available 24/7. You are not alone.", "crisis": True},
            "crisis": True
        }

    return {
        "reply": "Thank you for sharing that with me — whatever brought you here today, you're not alone in it. I'm here to listen without judgement, without rushing. Can you tell me a little more about what's been on your mind?",
        "biomarkers": {"stress": 3.0, "energy": 0.60, "pace": 130, "emotion": "neutral", "condition": "general",
                       "insight": "Initial assessment. Exploring presenting concerns.",
                       "psycho": PSYCHO_FACTS[now_ts() % len(PSYCHO_FACTS)], "crisis": False},
        "crisis": False
    }

# ─── CONDITION CARDS ──────────────────────────────────────────────
def _cond_cards():
    out = ""
    for key, c in PSYCH_CONDITIONS.items():
        syms  = "".join(f"<li>{s}</li>" for s in c["symptoms"][:4])
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

CONDITIONS_JS = json.dumps({
    k: {"name": v["name"], "icon": v["icon"], "color": v["color"],
        "symptoms": v["symptoms"], "techniques": v["techniques"],
        "phq_scale": v["phq_scale"], "description": v["description"]}
    for k, v in PSYCH_CONDITIONS.items()
})

AI_STATUS = "live" if GOOGLE_API_KEY else "demo"

# ─── HTML ─────────────────────────────────────────────────────────
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MindWell — Mental Health AI</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,400;1,300;1,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#07080f;--s1:#0d0f1a;--s2:#131525;--s3:#1a1d30;--s4:#222640;
  --accent:#5b6ef5;--a2:#8b9bf8;--glow:rgba(91,110,245,.18);
  --green:#2dd4a0;--amber:#f0b429;--coral:#f26a5e;
  --text:#d8ddf5;--sub:#636882;--muted:#3d4162;--border:rgba(255,255,255,.055);
  --r:14px;--font:'Plus Jakarta Sans',sans-serif;--serif:'Fraunces',serif
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:var(--font);overflow:hidden}
.blob{position:fixed;top:-100px;left:50%;transform:translateX(-50%);width:700px;height:500px;border-radius:50%;pointer-events:none;z-index:0;background:radial-gradient(ellipse at 50% 30%,rgba(91,110,245,.07) 0%,transparent 65%)}
.app{display:flex;height:100vh;position:relative;z-index:1;padding-top:52px}

/* ── NAV ── */
nav{position:fixed;top:0;left:0;right:0;height:52px;z-index:300;background:rgba(7,8,15,.92);backdrop-filter:blur(24px);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;padding:0 18px}
.logo{font-family:var(--serif);font-size:20px;font-style:italic;font-weight:300;color:var(--a2)}
.logo b{font-style:normal;color:var(--text);font-weight:400}
.nav-r{display:flex;align-items:center;gap:7px}
.pill{display:flex;border-radius:20px;border:1px solid var(--border);background:var(--s2);overflow:hidden}
.pill button{font-family:var(--font);font-size:11px;font-weight:500;padding:5px 12px;border:none;background:transparent;color:var(--sub);cursor:pointer;transition:.18s}
.pill button.on{background:var(--accent);color:#fff}
.pill.lang button.on{background:rgba(91,110,245,.28);color:var(--a2)}
.ai-badge{font-size:10px;padding:3px 9px;border-radius:20px;border:1px solid;cursor:default}
.ai-badge.live{border-color:rgba(45,212,160,.3);background:rgba(45,212,160,.1);color:var(--green)}
.ai-badge.demo{border-color:rgba(240,180,41,.3);background:rgba(240,180,41,.1);color:var(--amber)}
.user-badge{font-size:10px;padding:3px 9px;border-radius:20px;border:1px solid rgba(91,110,245,.3);background:rgba(91,110,245,.1);color:var(--a2);font-weight:600}

/* ── ONBOARDING — role only, no API key ── */
.ob-bg{position:fixed;inset:0;z-index:500;background:rgba(0,0,0,.88);backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center}
.ob-modal{background:var(--s1);border:1px solid var(--border);border-radius:24px;padding:40px 36px;max-width:500px;width:94%;text-align:center;animation:fadeUp .35s ease}
@keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}
.ob-icon{font-size:60px;margin-bottom:14px;display:block;filter:drop-shadow(0 0 24px rgba(91,110,245,.4))}
.ob-title{font-family:var(--serif);font-size:30px;font-weight:300;font-style:italic;margin-bottom:8px;color:var(--text)}
.ob-sub{font-size:13px;color:var(--sub);line-height:1.9;margin-bottom:28px;max-width:360px;margin-left:auto;margin-right:auto}
.ob-step{display:none}.ob-step.active{display:block}
.role-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.role-card{border:2px solid var(--border);border-radius:16px;padding:24px 16px;cursor:pointer;transition:.2s;background:var(--s2)}
.role-card:hover{border-color:var(--accent);background:var(--s3);transform:translateY(-2px)}
.role-card.chosen{border-color:var(--accent);background:var(--glow);box-shadow:0 0 20px var(--glow)}
.role-icon{font-size:40px;margin-bottom:10px;display:block}
.role-name{font-size:15px;font-weight:600;margin-bottom:5px}
.role-desc{font-size:12px;color:var(--sub);line-height:1.6}
/* Step 2 chips */
.ob-chips{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin:16px 0}
.ob-chip{font-size:13px;padding:9px 17px;border-radius:20px;border:1px solid var(--border);background:var(--s2);color:var(--sub);cursor:pointer;transition:.2s;font-family:var(--font)}
.ob-chip:hover{border-color:var(--accent);color:var(--a2);background:var(--glow)}
.ob-btn{width:100%;padding:12px;border:none;border-radius:12px;font-family:var(--font);font-size:14px;font-weight:600;cursor:pointer;transition:.2s}
.ob-btn.primary{background:var(--accent);color:#fff}
.ob-btn.primary:hover{background:var(--a2)}
.ob-btn.ghost{background:var(--s3);color:var(--sub);font-weight:400;font-size:13px;margin-top:8px}
.ob-btn.ghost:hover{color:var(--text)}

/* ── SIDEBAR ── */
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
.cond-card{display:flex;align-items:flex-start;gap:9px;padding:9px 10px;border-radius:10px;border:1px solid var(--border);background:var(--s2);margin-bottom:5px;cursor:pointer;transition:.18s}
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
.hist-item{padding:8px 10px;border-radius:10px;border:1px solid var(--border);background:var(--s2);margin-bottom:5px;cursor:pointer;transition:.18s}
.hist-item:hover{border-color:var(--accent)}
.hist-date{font-size:10px;color:var(--sub)}
.hist-prev{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}

/* ── CHAT ── */
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
.w-chip{font-size:12px;padding:8px 16px;border-radius:20px;border:1px solid var(--border);background:var(--s1);color:var(--sub);cursor:pointer;transition:.2s;font-family:var(--font)}
.w-chip:hover{border-color:var(--accent);color:var(--a2);background:var(--glow)}

/* ── INPUT ── */
.input-zone{padding:10px 18px 14px;border-top:1px solid var(--border);background:var(--bg);flex-shrink:0}
.emotion-row{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:8px;align-items:center}
.ec-l{font-size:10px;color:var(--sub)}
.chip{font-size:11px;padding:3px 10px;border-radius:20px;border:1px solid var(--border);background:var(--s2);color:var(--sub);cursor:pointer;transition:.18s;font-family:var(--font)}
.chip:hover,.chip.on{border-color:var(--accent);color:var(--a2);background:var(--glow)}
.irow{display:flex;align-items:flex-end;gap:7px;background:var(--s1);border:1px solid var(--border);border-radius:var(--r);padding:8px 10px;transition:.2s}
.irow:focus-within{border-color:var(--accent)}
#inp{flex:1;background:none;border:none;outline:none;color:var(--text);font-family:var(--font);font-size:14px;resize:none;max-height:100px;min-height:22px;line-height:1.55}
#inp::placeholder{color:var(--sub)}
.ico{width:31px;height:31px;border-radius:9px;border:1px solid var(--border);background:var(--s2);color:var(--sub);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:.18s;flex-shrink:0;font-size:15px;font-family:var(--font)}
.ico:hover{border-color:var(--accent);color:var(--a2)}
.ico.rec{border-color:var(--coral);color:var(--coral);animation:pulse 1s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.send-btn{width:31px;height:31px;border-radius:9px;border:none;background:var(--accent);color:#fff;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px;transition:.18s;font-family:var(--font)}
.send-btn:hover{background:var(--a2);transform:scale(1.06)}

/* ── BIO PANEL ── */
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
.ac-icon{font-size:20px}.ac-name{font-size:13px;font-weight:600;flex:1}
.ac-badge{font-size:9px;padding:2px 6px;border-radius:4px;background:var(--s4);color:var(--sub)}
.ac-syms{font-size:10px;color:var(--sub);padding-left:13px;line-height:1.9}
.ac-techs{display:flex;flex-wrap:wrap;gap:4px;margin-top:7px}
.ac-tech{font-size:10px;padding:2px 7px;border-radius:20px;border:1px solid rgba(91,110,245,.25);color:var(--a2);background:rgba(91,110,245,.08)}

/* ── DOCTOR / CONDITIONS ── */
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
.summary-box{background:rgba(91,110,245,.06);border-left:3px solid var(--accent);padding:12px 14px;border-radius:4px;font-size:13px;line-height:1.82;color:var(--text)}
.sum-btn{margin-top:12px;width:100%;padding:9px;background:var(--accent);border:none;border-radius:10px;color:#fff;font-family:var(--font);font-size:13px;cursor:pointer;font-weight:500;transition:.18s}
.sum-btn:hover{background:var(--a2)}

/* ── CRISIS MODAL ── */
.modal-bg{display:none;position:fixed;inset:0;z-index:600;background:rgba(0,0,0,.8);backdrop-filter:blur(6px);align-items:center;justify-content:center}
.modal-bg.show{display:flex}
.modal{background:var(--s1);border:1px solid rgba(242,106,94,.25);border-radius:20px;padding:26px;max-width:340px;width:92%;text-align:center;animation:fadeUp .3s ease}
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

<!-- ══ ONBOARDING — role selection only, no API key ══ -->
<div class="ob-bg" id="ob-bg">
  <div class="ob-modal">

    <!-- Step 1: Choose role -->
    <div class="ob-step active" id="ob-step-1">
      <span class="ob-icon">🧠</span>
      <div class="ob-title">Welcome to MindWell</div>
      <div class="ob-sub">Expert mental health support across 16 psychological conditions. First, tell us who you are so we can personalise your experience.</div>
      <div class="role-grid">
        <div class="role-card" id="rc-patient" onclick="chooseRole('patient')">
          <span class="role-icon">🙋</span>
          <div class="role-name">I'm a Patient</div>
          <div class="role-desc">Seeking support for my own mental health, emotions, or a specific condition</div>
        </div>
        <div class="role-card" id="rc-doctor" onclick="chooseRole('doctor')">
          <span class="role-icon">🩺</span>
          <div class="role-name">I'm a Doctor</div>
          <div class="role-desc">Mental health professional using this as a clinical support and assessment tool</div>
        </div>
      </div>
    </div>

    <!-- Step 2a: Patient — what's on your mind -->
    <div class="ob-step" id="ob-step-patient">
      <span class="ob-icon">💬</span>
      <div class="ob-title">What's on your mind?</div>
      <div class="ob-sub">Choose what you're experiencing, or just start typing. MindWell will detect and adapt to your condition automatically.</div>
      <div class="ob-chips">
        <div class="ob-chip" onclick="obStart('I have been feeling very anxious and cannot stop worrying')">😰 Anxiety</div>
        <div class="ob-chip" onclick="obStart('I feel very low and hopeless, like nothing matters')">😔 Depression</div>
        <div class="ob-chip" onclick="obStart('I keep having intrusive thoughts I cannot control')">🔄 OCD</div>
        <div class="ob-chip" onclick="obStart('I had a panic attack and I am scared it will happen again')">💨 Panic</div>
        <div class="ob-chip" onclick="obStart('Work has completely burned me out and I feel empty inside')">🔥 Burnout</div>
        <div class="ob-chip" onclick="obStart('I cannot sleep no matter what I try')">😴 Sleep Issues</div>
        <div class="ob-chip" onclick="obStart('I am grieving and struggling to cope with the loss')">🕊️ Grief</div>
        <div class="ob-chip" onclick="obStart('I feel completely alone and disconnected from everyone')">🥺 Loneliness</div>
        <div class="ob-chip" onclick="obStart('I have been through something traumatic and I am not okay')">⚡ PTSD / Trauma</div>
        <div class="ob-chip" onclick="obStart('I cannot focus or stay organised, it is affecting everything')">🎯 ADHD</div>
        <div class="ob-chip" onclick="obStart('I am struggling with addiction and want help')">🔗 Addiction</div>
        <div class="ob-chip" onclick="obStart('My moods swing dramatically and I feel out of control')">🌊 Mood Swings</div>
      </div>
      <button class="ob-btn ghost" onclick="closeOb()">Just open the chat — I'll type</button>
    </div>

    <!-- Step 2b: Doctor -->
    <div class="ob-step" id="ob-step-doctor">
      <span class="ob-icon">🩺</span>
      <div class="ob-title">Clinical Dashboard Ready</div>
      <div class="ob-sub">You have access to the full clinical suite — patient management, PHQ-9 / GAD-7 assessments, and AI-generated session summaries.</div>
      <div class="ob-chips">
        <div class="ob-chip" onclick="docStart('anxiety')">📋 Anxiety — GAD-7</div>
        <div class="ob-chip" onclick="docStart('depression')">📋 Depression — PHQ-9</div>
        <div class="ob-chip" onclick="docStart('ptsd')">📋 PTSD — PCL-5</div>
        <div class="ob-chip" onclick="docStart('ocd')">📋 OCD — OCI-R</div>
        <div class="ob-chip" onclick="docStart('bipolar')">📋 Bipolar — MDQ</div>
        <div class="ob-chip" onclick="docStart('adhd')">📋 ADHD — ASRS</div>
      </div>
      <div style="display:flex;gap:8px;margin-top:8px">
        <button class="ob-btn primary" style="flex:1" onclick="openDash()">Open Clinical Dashboard</button>
        <button class="ob-btn ghost" style="flex:1;margin-top:0" onclick="closeOb()">Open Chat</button>
      </div>
    </div>

  </div>
</div>

<!-- ══ NAV ══ -->
<nav>
  <div class="logo">Mind<b>Well</b></div>
  <div class="nav-r">
    <span class="user-badge" id="ut-badge">🙋 Patient</span>
    <div class="ai-badge __AI_STATUS__" id="ai-badge">● __AI_LABEL__</div>
    <div class="pill lang" id="lang-pill">
      <button class="on" onclick="setLang('en',this)">EN</button>
      <button onclick="setLang('hi',this)">हिं</button>
      <button onclick="setLang('mr',this)">मर</button>
      <button onclick="setLang('ta',this)">தமி</button>
    </div>
    <div class="pill">
      <button class="on" id="btn-chat" onclick="setMode('chat')">Chat</button>
      <button id="btn-conditions" onclick="setMode('conditions')">Conditions</button>
      <button id="btn-doctor" onclick="setMode('doctor')">Doctor</button>
    </div>
  </div>
</nav>

<!-- ══ APP ══ -->
<div class="app">

  <!-- SIDEBAR -->
  <div class="sidebar">
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
      <div id="hist-list"><div style="font-size:12px;color:var(--sub)">No sessions yet — start chatting!</div></div>
    </div>
    <div class="sc" id="tab-conds" style="display:none">
      <div class="sec-l">Select condition</div>
      __CONDITION_CARDS__
    </div>
  </div>

  <!-- CENTRE -->
  <div class="chat" id="chat-area">

    <!-- CHAT VIEW -->
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
            <div class="w-chip" onclick="qs('I had a panic attack and I am scared it will happen again')">💨 Panic</div>
            <div class="w-chip" onclick="qs('Work has completely burned me out')">🔥 Burnout</div>
            <div class="w-chip" onclick="qs('I cannot sleep no matter what I try')">😴 Sleep Issues</div>
            <div class="w-chip" onclick="qs('I am grieving and struggling to cope')">🕊️ Grief</div>
            <div class="w-chip" onclick="qs('I feel completely alone and disconnected from everyone')">🥺 Loneliness</div>
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

    <!-- CONDITIONS ENCYCLOPAEDIA -->
    <div id="conds-view" style="display:none;flex:1;overflow-y:auto;padding:18px 20px">
      <div style="font-family:var(--serif);font-size:24px;font-weight:300;font-style:italic">16 Psychological Conditions</div>
      <div style="font-size:13px;color:var(--sub);margin-top:6px">Click any condition to start a guided conversation</div>
      <div class="enc-grid" id="enc-grid"></div>
    </div>

    <!-- DOCTOR DASHBOARD -->
    <div id="doc-view">
      <div style="font-family:var(--serif);font-size:24px;font-weight:300;font-style:italic;padding:18px 20px 0">Clinical Dashboard</div>
      <div style="padding:14px 20px;display:flex;flex-direction:column;gap:12px;overflow-y:auto;flex:1">
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
            <div class="phq-r"><span class="phq-q">Tired or low energy</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
            <div class="phq-r"><span class="phq-q">Poor appetite or overeating</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
            <div class="phq-r"><span class="phq-q">Feeling bad about yourself</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
            <div class="phq-r"><span class="phq-q">Trouble concentrating</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
            <div class="phq-r"><span class="phq-q">Moving slowly or restless</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
            <div class="phq-r"><span class="phq-q">Thoughts of self-harm</span><div class="phq-sc"><span class="ps" onclick="phqS(this)">0</span><span class="ps" onclick="phqS(this)">1</span><span class="ps" onclick="phqS(this)">2</span><span class="ps" onclick="phqS(this)">3</span></div></div>
            <div class="phq-tot"><span style="font-size:12px;color:var(--sub)">PHQ-9 Total</span><span style="font-size:22px;font-weight:600;color:var(--amber)" id="phq-t">0</span></div>
          </div>
          <div class="doc-card" style="grid-column:1/-1">
            <div class="dc-h">AI Session Summary</div>
            <div class="summary-box" id="doc-summary">Use the chat with a patient, then click Generate Summary to create a clinical session note.</div>
            <button class="sum-btn" onclick="genSummary()">Generate AI Summary from Current Chat</button>
          </div>
        </div>
      </div>
    </div>

  </div>

  <!-- BIO PANEL -->
  <div class="bio-panel">
    <div>
      <div class="bp-sec">Active condition</div>
      <div class="ac-card" id="ac-panel">
        <div class="ac-hdr"><span class="ac-icon">🧠</span><span class="ac-name">General Support</span></div>
        <div class="txt-sm">Start chatting — I'll detect your condition automatically.</div>
      </div>
    </div>
    <div>
      <div class="bp-sec">Session signals</div>
      <div class="bm-card"><div class="bm-lbl">Stress index</div><div class="bm-val" id="bm-s" style="color:var(--amber)">—</div><div class="bm-desc" id="bm-sd">Waiting for first message</div></div>
      <div class="bm-card"><div class="bm-lbl">Emotional energy</div><div class="bm-val" id="bm-e" style="color:var(--a2)">—</div><div class="bm-desc">Updates after first reply</div></div>
      <div class="bm-card"><div class="bm-lbl">Speech pace</div><div class="bm-val" id="bm-p" style="color:var(--green)">—</div><div class="bm-desc">wpm estimate</div></div>
    </div>
    <div><div class="bp-sec">Status</div><div class="status-box s-calm" id="status-box">Awaiting session start</div></div>
    <div><div class="bp-sec">Session insight</div><div class="txt-sm" id="insight-txt">Insights appear as the session develops.</div></div>
    <div><div class="bp-sec">Psychoeducation</div><div class="txt-sm" id="psycho-txt">Anxiety activates the amygdala. Deep breathing activates the parasympathetic system and lowers cortisol in under 60 seconds.</div></div>
  </div>

</div>

<!-- CRISIS MODAL -->
<div class="modal-bg" id="crisis-modal">
  <div class="modal">
    <div style="font-size:40px">💙</div>
    <h2>We're here for you</h2>
    <p>You're not alone. Please reach out — these helplines are confidential and free.</p>
    <div class="helpline">iCall (Mon–Sat, 8am–10pm)<strong>9152987821</strong></div>
    <div class="helpline">NIMHANS Helpline<strong>080-46110007</strong></div>
    <div class="helpline">Vandrevala Foundation (24/7)<strong>1860-2662-345</strong></div>
    <button class="mc" onclick="closeCrisis()">I'll reach out — thank you</button>
  </div>
</div>

<script>
const CONDITIONS = __CONDITIONS_JS__;
let history=[], lang='en', mood='', userType='patient',
    recording=false, speechRec=null, activeCond=null, sessions=[];

// ── ONBOARDING ──────────────────────────────────────────────────
function chooseRole(role){
  userType = role;
  document.getElementById('ut-badge').textContent = role==='doctor' ? '🩺 Doctor' : '🙋 Patient';
  document.querySelectorAll('.role-card').forEach(c=>c.classList.remove('chosen'));
  document.getElementById('rc-'+role).classList.add('chosen');
  setTimeout(()=>{
    document.querySelectorAll('.ob-step').forEach(s=>s.classList.remove('active'));
    document.getElementById('ob-step-'+role).classList.add('active');
  }, 260);
}

function obStart(text){
  document.getElementById('ob-bg').style.display='none';
  sendText(text);
}

function docStart(cond){
  document.getElementById('ob-bg').style.display='none';
  activeCond = cond;
  setMode('doctor');
  const c = CONDITIONS[cond];
  if(c){
    setTimeout(()=>{
      setMode('chat');
      sendText(`I'd like to conduct a clinical assessment for ${c.name} using the ${c.phq_scale} scale. Please guide me through key screening questions.`);
    }, 100);
  }
}

function openDash(){
  document.getElementById('ob-bg').style.display='none';
  setMode('doctor');
}

function closeOb(){
  document.getElementById('ob-bg').style.display='none';
  if(!document.getElementById('msgs').querySelector('.msg')){
    addMsg('a', "Hello, welcome to MindWell. I'm here to listen without judgement — whatever you're carrying right now, you don't have to face it alone. What's been on your mind lately?", 'neutral', null);
  }
}

// ── NAV / MODES ─────────────────────────────────────────────────
function setLang(l,btn){
  lang=l;
  document.querySelectorAll('#lang-pill button').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
}

function setMode(m){
  ['chat','conditions','doctor'].forEach(id=>{
    const b=document.getElementById('btn-'+id); if(b) b.classList.remove('on');
  });
  const btn=document.getElementById('btn-'+m); if(btn) btn.classList.add('on');
  document.getElementById('chat-view').style.display    = m==='chat' ? 'flex' : 'none';
  document.getElementById('chat-view').style.flexDirection = 'column';
  document.getElementById('conds-view').style.display   = m==='conditions' ? 'block' : 'none';
  const dv = document.getElementById('doc-view');
  dv.style.display = m==='doctor' ? 'flex' : 'none';
  dv.style.flexDirection = 'column';
  if(m==='conditions') buildEnc();
}

function switchTab(tab,btn){
  document.querySelectorAll('.stab').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  ['mood','history','conds'].forEach(t=>{
    document.getElementById('tab-'+t).style.display = t===tab ? 'block' : 'none';
  });
  if(tab==='history') renderHistory();
}

// ── CONDITIONS ──────────────────────────────────────────────────
function selectCond(key){
  activeCond = key;
  document.querySelectorAll('.cond-card').forEach(c=>c.classList.toggle('active',c.dataset.key===key));
  updateAC(key);
  setMode('chat');
  document.getElementById('btn-chat').classList.add('on');
  const c = CONDITIONS[key];
  if(c) sendText(`I think I might be dealing with ${c.name}. Can you help me understand what it is and how to manage it?`);
}

function updateAC(key){
  const p = document.getElementById('ac-panel');
  if(!key||!CONDITIONS[key]){
    p.innerHTML='<div class="ac-hdr"><span class="ac-icon">🧠</span><span class="ac-name">General Support</span></div><div class="txt-sm">Start chatting — condition detected automatically.</div>';
    return;
  }
  const c=CONDITIONS[key];
  const syms=c.symptoms.map(s=>`<li>${s}</li>`).join('');
  const techs=c.techniques.map(t=>`<span class="ac-tech">${t}</span>`).join('');
  p.innerHTML=`<div class="ac-hdr"><span class="ac-icon">${c.icon}</span><span class="ac-name">${c.name}</span><span class="ac-badge">${c.phq_scale}</span></div><ul class="ac-syms">${syms}</ul><div class="ac-techs">${techs}</div>`;
}

function buildEnc(){
  const g=document.getElementById('enc-grid');
  if(g.children.length>0) return;
  Object.entries(CONDITIONS).forEach(([key,c])=>{
    const d=document.createElement('div');d.className='enc-card';
    d.innerHTML=`<div class="enc-icon">${c.icon}</div><div class="enc-name">${c.name}</div><div class="enc-desc">${c.description}</div><span class="enc-tag">${c.phq_scale}</span>`;
    d.onclick=()=>selectCond(key); g.appendChild(d);
  });
}

// ── MOOD ────────────────────────────────────────────────────────
function pickMood(btn,emoji,label){
  document.querySelectorAll('.mb').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on'); mood=label;
  document.getElementById('mood-lbl').textContent='Feeling: '+emoji+' '+label;
}

// ── CHAT ────────────────────────────────────────────────────────
function toggleChip(el){ el.classList.toggle('on'); }
function qs(t){ document.getElementById('inp').value=t; sendMsg(); }
function onKey(e){ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg();} }
function rsz(el){ el.style.height='auto'; el.style.height=Math.min(el.scrollHeight,100)+'px'; }

function sendText(text){
  const w=document.getElementById('welcome'); if(w) w.remove();
  document.getElementById('inp').value=text; sendMsg();
}

async function sendMsg(){
  const el=document.getElementById('inp'), text=el.value.trim();
  if(!text) return;
  const w=document.getElementById('welcome'); if(w) w.remove();
  el.value=''; el.style.height='auto';
  addMsg('u', text);
  history.push({role:'user', content:text});
  animScores();
  document.getElementById('typing').classList.add('show');
  scrollBot();
  try{
    const r=await fetch('/api/chat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        message:text,
        history:history.slice(-12),
        language:lang,
        mood:mood,
        condition_hint:activeCond||'',
        user_type:userType
      })
    });
    if(!r.ok) throw new Error('HTTP '+r.status);
    const d=await r.json();
    document.getElementById('typing').classList.remove('show');
    addMsg('a', d.reply, d.biomarkers?.emotion, d.biomarkers?.condition);
    if(d.biomarkers) updateBio(d.biomarkers);
    if(d.crisis) showCrisis();
    history.push({role:'assistant',content:d.reply});
    saveSession(text, d.reply);
  }catch(e){
    document.getElementById('typing').classList.remove('show');
    addMsg('a','Something went wrong. Please check your connection and try again.');
  }
  scrollBot();
}

function addMsg(role,text,emotion,condition){
  const msgs=document.getElementById('msgs'),div=document.createElement('div');
  div.className='msg '+role;
  const badge=(role==='a'&&emotion&&emotion!=='neutral')?
    `<div class="e-badge"><span class="e-dot"></span>Detected: ${emotion}</div>`:'';
  let cb='';
  if(role==='a'&&condition&&condition!=='general'&&CONDITIONS[condition]){
    const c=CONDITIONS[condition];
    cb=`<div class="cond-banner"><span>${c.icon}</span>${c.name} identified</div>`;
    if(activeCond!==condition){
      activeCond=condition; updateAC(condition);
      document.querySelectorAll('.cond-card').forEach(cc=>cc.classList.toggle('active',cc.dataset.key===condition));
    }
  }
  const t=new Date().toLocaleTimeString('en-IN',{hour:'2-digit',minute:'2-digit'});
  div.innerHTML=`${cb}${badge}<div class="bubble">${text.replace(/\n/g,'<br>')}</div><div class="msg-time">${t}</div>`;
  msgs.appendChild(div); scrollBot();
}

function scrollBot(){ const m=document.getElementById('msgs'); if(m) m.scrollTop=m.scrollHeight; }

// ── BIOMARKERS ──────────────────────────────────────────────────
function updateBio(b){
  const s=parseFloat(b.stress)||3;
  const el=document.getElementById('bm-s');
  el.textContent=s.toFixed(1);
  el.style.color=s>6.5?'var(--coral)':s>4.5?'var(--amber)':'var(--green)';
  document.getElementById('bm-sd').textContent=s>6.5?'High distress':s>4.5?'Moderate tension':'Low stress';
  if(b.energy!==undefined) document.getElementById('bm-e').textContent=parseFloat(b.energy).toFixed(2);
  if(b.pace) document.getElementById('bm-p').textContent=Math.round(b.pace);
  if(b.insight) document.getElementById('insight-txt').textContent=b.insight;
  if(b.psycho) document.getElementById('psycho-txt').textContent=b.psycho;
  const box=document.getElementById('status-box');
  if(s>7.5){box.className='status-box s-crisis';box.textContent='⚠️ High distress. Clinical check-in recommended.';}
  else if(s>5){box.className='status-box s-warn';box.textContent='🔶 Elevated stress signals.';}
  else{box.className='status-box s-calm';box.textContent='✅ Stable signals.';}
}

function animScores(){
  const cl=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
  let a=parseFloat(document.getElementById('anx-v').textContent)||4;
  let mo=parseFloat(document.getElementById('mood-v').textContent)||7;
  let st=parseFloat(document.getElementById('stress-v').textContent)||3;
  a=cl(a+(Math.random()>.55?.3:-.2),1,9.5);
  mo=cl(mo+(Math.random()>.45?.2:-.15),1,9.5);
  st=cl(st+(Math.random()>.5?.25:-.2),1,9.5);
  document.getElementById('anx-v').textContent=a.toFixed(1);
  document.getElementById('mood-v').textContent=mo.toFixed(1);
  document.getElementById('stress-v').textContent=st.toFixed(1);
  document.getElementById('anx-b').style.width=(a/10*100)+'%';
  document.getElementById('mood-b').style.width=(mo/10*100)+'%';
  document.getElementById('stress-b').style.width=(st/10*100)+'%';
}

// ── SESSION HISTORY ──────────────────────────────────────────────
function saveSession(userMsg, aiMsg){
  const today=new Date().toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'});
  if(!sessions.length||sessions[0].date!==today){
    sessions.unshift({date:today, preview:userMsg.substring(0,40)+'…', msgs:[]});
  }
  sessions[0].msgs.push({r:'u',t:userMsg},{r:'a',t:aiMsg});
}

function renderHistory(){
  const el=document.getElementById('hist-list'); el.innerHTML='';
  if(!sessions.length){
    el.innerHTML='<div style="font-size:12px;color:var(--sub)">No sessions yet — start chatting!</div>';
    return;
  }
  sessions.forEach((s,i)=>{
    const d=document.createElement('div'); d.className='hist-item';
    d.innerHTML=`<div class="hist-date">${s.date}</div><div style="font-size:12px;color:var(--text);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${s.preview}</div>`;
    d.onclick=()=>{
      document.getElementById('msgs').innerHTML='';
      s.msgs.forEach(m=>addMsg(m.r,m.t));
      history=s.msgs.map(m=>({role:m.r==='a'?'assistant':'user',content:m.t}));
      setMode('chat'); document.getElementById('btn-chat').classList.add('on');
    };
    el.appendChild(d);
  });
}

// ── DOCTOR SUMMARY ──────────────────────────────────────────────
async function genSummary(){
  if(!history.length){document.getElementById('doc-summary').textContent='No conversation yet. Chat with a patient first.';return;}
  document.getElementById('doc-summary').textContent='Generating clinical summary…';
  try{
    const r=await fetch('/api/summary',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({messages:history})});
    const d=await r.json();
    document.getElementById('doc-summary').innerHTML=d.summary.replace(/\n/g,'<br>');
  }catch(e){document.getElementById('doc-summary').textContent='Error generating summary. Please try again.';}
}

// ── PHQ ──────────────────────────────────────────────────────────
function phqS(el){
  el.parentElement.querySelectorAll('.ps').forEach(s=>s.classList.remove('on')); el.classList.add('on');
  let t=0; document.querySelectorAll('.ps.on').forEach(s=>t+=parseInt(s.textContent));
  const v=document.getElementById('phq-t'); v.textContent=t;
  v.style.color=t<=4?'var(--green)':t<=9?'var(--amber)':'var(--coral)';
}

// ── MIC ──────────────────────────────────────────────────────────
function toggleMic(){
  const btn=document.getElementById('mic-btn'); recording=!recording;
  btn.classList.toggle('rec',recording); btn.textContent=recording?'⏹️':'🎙️';
  if(recording){
    const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(SR){
      speechRec=new SR(); speechRec.lang=lang==='hi'?'hi-IN':lang==='mr'?'mr-IN':lang==='ta'?'ta-IN':'en-IN';
      speechRec.onresult=e=>{document.getElementById('inp').value=e.results[0][0].transcript;if(recording)toggleMic();};
      speechRec.onerror=()=>{if(recording)toggleMic();};
      speechRec.start();
    }else{alert('Speech recognition not supported in this browser. Please use Chrome.');}
  }else{if(speechRec){try{speechRec.stop();}catch(e){}speechRec=null;}}
}

// ── CRISIS ──────────────────────────────────────────────────────
function showCrisis(){ document.getElementById('crisis-modal').classList.add('show'); }
function closeCrisis(){ document.getElementById('crisis-modal').classList.remove('show'); }
</script>
</body>
</html>"""

def get_html():
    ai_label = "● Gemini Live" if GOOGLE_API_KEY else "● Demo Mode"
    ai_status = "live" if GOOGLE_API_KEY else "demo"
    return (HTML_TEMPLATE
            .replace("__CONDITION_CARDS__", _cond_cards())
            .replace("__CONDITIONS_JS__",   CONDITIONS_JS)
            .replace("__AI_STATUS__",       ai_status)
            .replace("__AI_LABEL__",        ai_label))

# ─── STATUS CODES ─────────────────────────────────────────────────
STATUS_TEXTS = {
    200:"200 OK", 201:"201 Created", 204:"204 No Content",
    400:"400 Bad Request", 401:"401 Unauthorized", 404:"404 Not Found",
    405:"405 Method Not Allowed", 410:"410 Gone", 500:"500 Internal Server Error",
}

# ─── ROUTER ───────────────────────────────────────────────────────
def route(method, path, body):
    h = cors()

    if method == "GET" and path in ("/", ""):
        return get_html(), 200, {**h, "Content-Type": "text/html; charset=utf-8"}

    if method == "OPTIONS":
        return "", 204, h

    if method == "POST" and path == "/api/chat":
        msg = body.get("message", "").strip()
        if not msg:
            return json_resp({"error": "message required"}, 400)
        result = gemini_chat(
            msg,
            body.get("history", []),
            body.get("language", "en"),
            body.get("mood", ""),
            body.get("condition_hint", ""),
            body.get("user_type", "patient"),
        )
        crisis = detect_crisis(msg) or result.get("crisis", False)
        return json_resp({
            "reply":      result.get("reply", ""),
            "biomarkers": result.get("biomarkers", {}),
            "crisis":     crisis,
        })

    if method == "POST" and path == "/api/summary":
        return json_resp({"summary": gemini_summary(body.get("messages", []))})

    if method == "POST" and path == "/api/mood":
        e = {
            "id":        new_id(),
            "user_id":   body.get("user_id", "anon"),
            "emoji":     body.get("emoji", "😐"),
            "label":     body.get("label", "Neutral"),
            "anxiety":   float(body.get("anxiety", 5)),
            "mood":      float(body.get("mood", 5)),
            "stress":    float(body.get("stress", 5)),
            "logged_at": datetime.utcnow().isoformat(),
        }
        MOOD_LOGS.append(e)
        return json_resp({"ok": True, "entry": e})

    if method == "GET" and path == "/api/conditions":
        return json_resp({"conditions": {
            k: {"name":v["name"],"icon":v["icon"],"description":v["description"],
                "symptoms":v["symptoms"],"techniques":v["techniques"],"phq_scale":v["phq_scale"]}
            for k,v in PSYCH_CONDITIONS.items()
        }})

    if method == "GET" and path == "/api/health":
        return json_resp({
            "status": "ok", "service": "MindWell v4.0",
            "ai_ready": bool(GOOGLE_API_KEY),
            "conditions": len(PSYCH_CONDITIONS),
        })

    return json_resp({"error": "Not found"}, 404)

# ─── VERCEL WSGI ──────────────────────────────────────────────────
def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET")
    path   = environ.get("PATH_INFO", "/")
    body   = {}
    if method in ("POST", "PUT", "PATCH"):
        try:
            length = int(environ.get("CONTENT_LENGTH", 0) or 0)
            raw    = environ["wsgi.input"].read(length)
            body   = json.loads(raw) if raw else {}
        except Exception:
            body = {}
    resp_body, status_code, headers = route(method, path, body)
    status_str  = STATUS_TEXTS.get(status_code, f"{status_code} Unknown")
    header_list = [(k, v) for k, v in headers.items()]
    start_response(status_str, header_list)
    if isinstance(resp_body, str):
        resp_body = resp_body.encode("utf-8")
    return [resp_body]

handler = app  # Vercel looks for this

# ─── LOCAL DEV ────────────────────────────────────────────────────
if __name__ == "__main__":
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import urlparse
    PORT = int(os.environ.get("PORT", 3000))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            print(f"  {self.command} {self.path} → {args[1]}")
        def _body(self):
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n) if n else b""
            try:    return json.loads(raw)
            except: return {}
        def _handle(self):
            path = urlparse(self.path).path
            body = self._body() if self.command in ("POST","PUT","PATCH") else {}
            resp_body, status_code, headers = route(self.command, path, body)
            if isinstance(resp_body, str): resp_body = resp_body.encode("utf-8")
            self.send_response(status_code)
            for k, v in headers.items(): self.send_header(k, v)
            self.send_header("Content-Length", len(resp_body))
            self.end_headers()
            self.wfile.write(resp_body)
        def do_GET(self):    self._handle()
        def do_POST(self):   self._handle()
        def do_OPTIONS(self):self._handle()

    key_status = "SET ✅" if GOOGLE_API_KEY else "NOT SET — demo mode ⚠️"
    print(f"""
  MindWell v4.0  →  http://localhost:{PORT}
  API Key        →  {key_status}
  Conditions     →  {len(PSYCH_CONDITIONS)}
  Endpoints      →  / | /api/chat | /api/summary | /api/health
""")
    HTTPServer(("", PORT), Handler).serve_forever()
