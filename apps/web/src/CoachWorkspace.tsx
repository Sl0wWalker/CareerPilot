import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "./api";

type Dashboard = {
  active_goals: number;
  completed_sessions: number;
  average_interview_score: number | null;
  active_learning_plans: number;
  next_actions: string[];
};
type Goal = { id: string; title: string; description: string; status: string };
type Question = {
  id: string;
  category: string;
  question: string;
  rationale: string;
  difficulty: string;
};
type Plan = {
  id: string;
  title: string;
  target_role: string;
  gap_analysis: Array<Record<string, unknown>>;
  recommendations: Array<Record<string, unknown>>;
};

export function CoachWorkspace() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [goals, setGoals] = useState<Goal[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [goalTitle, setGoalTitle] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    const responses = await Promise.all([
      apiFetch("/coach/dashboard"),
      apiFetch("/coach/goals"),
      apiFetch("/coach/learning-plans"),
    ]);
    if (responses[0].ok) setDashboard(await responses[0].json());
    if (responses[1].ok) setGoals(await responses[1].json());
    if (responses[2].ok) setPlans(await responses[2].json());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function addGoal() {
    if (!goalTitle.trim()) return;
    const response = await apiFetch("/coach/goals", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: goalTitle, description: "", priority: 3 }),
    });
    setMessage(response.ok ? "Career goal added." : "Could not add the goal.");
    if (response.ok) {
      setGoalTitle("");
      await load();
    }
  }

  async function prepareInterview() {
    const response = await apiFetch("/coach/interview/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        categories: ["behavioral", "technical", "company", "resume"],
        count: 10,
      }),
    });
    if (response.ok) {
      setQuestions(await response.json());
      setMessage("Interview practice set is ready.");
    } else {
      setMessage("Create a verified career profile and check the AI provider.");
    }
  }

  async function createPlan() {
    if (!targetRole.trim()) return;
    const response = await apiFetch("/coach/learning-plans", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_role: targetRole }),
    });
    setMessage(
      response.ok ? "Learning plan created." : "Could not create the plan.",
    );
    if (response.ok) {
      setTargetRole("");
      await load();
    }
  }

  return (
    <section className="coach-workspace">
      <section className="hero">
        <p className="eyebrow">AI CAREER COACH</p>
        <h1>Turn verified experience into a practical career plan.</h1>
        <p className="lede">
          Prepare for interviews, strengthen STAR stories, close evidence-backed
          skill gaps, compare offers, and plan your next move.
        </p>
      </section>

      <div className="coach-metrics">
        <article className="panel">
          <strong>{dashboard?.active_goals ?? 0}</strong>
          <span>Active goals</span>
        </article>
        <article className="panel">
          <strong>{dashboard?.completed_sessions ?? 0}</strong>
          <span>Mock interviews</span>
        </article>
        <article className="panel">
          <strong>{dashboard?.average_interview_score ?? "—"}</strong>
          <span>Interview score</span>
        </article>
        <article className="panel">
          <strong>{dashboard?.active_learning_plans ?? 0}</strong>
          <span>Learning plans</span>
        </article>
      </div>

      <div className="coach-grid">
        <article className="panel">
          <p className="eyebrow">CAREER ROADMAP</p>
          <h2>Goals and next actions</h2>
          <div className="search-row">
            <input
              aria-label="Career goal"
              value={goalTitle}
              onChange={(event) => setGoalTitle(event.target.value)}
              placeholder="e.g. Become a formal verification lead"
            />
            <button
              type="button"
              className="button"
              onClick={() => void addGoal()}
            >
              Add goal
            </button>
          </div>
          {goals.map((goal) => (
            <div className="coach-row" key={goal.id}>
              <strong>{goal.title}</strong>
              <span>{goal.status}</span>
            </div>
          ))}
          {dashboard?.next_actions.map((action) => (
            <p className="muted" key={action}>
              → {action}
            </p>
          ))}
        </article>

        <article className="panel">
          <p className="eyebrow">INTERVIEW PREP</p>
          <h2>Company, behavioral, and technical practice</h2>
          <p className="muted">
            Questions are grounded in your verified Career Knowledge Base.
          </p>
          <button
            type="button"
            className="button"
            onClick={() => void prepareInterview()}
          >
            Generate practice set
          </button>
        </article>

        <article className="panel">
          <p className="eyebrow">LEARNING PLAN</p>
          <h2>Close the right skill gaps</h2>
          <div className="search-row">
            <input
              aria-label="Target role"
              value={targetRole}
              onChange={(event) => setTargetRole(event.target.value)}
              placeholder="Target role"
            />
            <button
              type="button"
              className="button"
              onClick={() => void createPlan()}
            >
              Build plan
            </button>
          </div>
          {plans.map((plan) => (
            <div className="coach-row" key={plan.id}>
              <strong>{plan.title}</strong>
              <span>{plan.recommendations.length} actions</span>
            </div>
          ))}
        </article>
      </div>

      {message && <p className="muted">{message}</p>}
      {questions.length > 0 && (
        <section className="panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">MOCK INTERVIEW</p>
              <h2>Practice questions</h2>
            </div>
            <span>{questions.length}</span>
          </div>
          <div className="suggestions">
            {questions.map((question) => (
              <article className="suggestion" key={question.id}>
                <div>
                  <strong>{question.category}</strong>
                  <span>{question.difficulty}</span>
                </div>
                <h3>{question.question}</h3>
                <p>{question.rationale}</p>
              </article>
            ))}
          </div>
        </section>
      )}
    </section>
  );
}
