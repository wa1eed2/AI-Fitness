import {
  useEffect,
  useState
} from "react";

import {
  Link
} from "react-router-dom";

import {
  useAuth
} from "../auth/AuthContext";

import {
  ApiError,
  listVisionAnalyses,
  VisionAnalysisSummary
} from "../lib/api";


export function DashboardPage() {
  const {
    session
  } = useAuth();

  const [
    analyses,
    setAnalyses
  ] = useState<VisionAnalysisSummary[]>(
    []
  );

  const [
    loading,
    setLoading
  ] = useState(true);

  const [
    error,
    setError
  ] = useState<string | null>(
    null
  );

  useEffect(
    () => {
      if (!session) {
        setLoading(
          false
        );

        return;
      }

      const accessToken = session.accessToken;

      let cancelled = false;

      async function loadDashboard() {
        try {
          const loaded = await listVisionAnalyses(
            accessToken,
            5
          );

          if (!cancelled) {
            setAnalyses(
              loaded
            );

            setError(
              null
            );
          }

        } catch (caughtError) {
          if (!cancelled) {
            setError(
              caughtError instanceof ApiError
              ? caughtError.message
              : "Unable to load dashboard data."
            );
          }

        } finally {
          if (!cancelled) {
            setLoading(
              false
            );
          }
        }
      }

      void loadDashboard();

      return () => {
        cancelled = true;
      };
    },
    [
      session
    ]
  );

  const totalReps = analyses.reduce(
    (
      total,
      analysis
    ) => (
      total
      + analysis.rep_count
    ),
    0
  );

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Dashboard
          </p>

          <h1>
            Training overview
          </h1>

          <p className="muted">
            Your fitness data stays
            separate from scientific
            evidence used by the AI coach.
          </p>
        </div>
      </header>

      <section className="metric-grid">
        <article className="metric-card">
          <span>
            Recent CV analyses
          </span>

          <strong>
            {
              loading
              ? "—"
              : analyses.length
            }
          </strong>
        </article>

        <article className="metric-card">
          <span>
            Reps in recent analyses
          </span>

          <strong>
            {
              loading
              ? "—"
              : totalReps
            }
          </strong>
        </article>

        <article className="metric-card">
          <span>
            CV processing
          </span>

          <strong>
            Local
          </strong>
        </article>
      </section>

      {error && (
        <div className="error-box">
          {error}
        </div>
      )}

      <section className="panel">
        <div className="panel-heading">
          <div>
            <h2>
              Movement analysis
            </h2>

            <p className="muted">
              Analyze squat repetitions,
              timing, observable geometry,
              and confidence.
            </p>
          </div>

          <Link
            className="primary-link"
            to="/app/vision"
          >
            Analyze video
          </Link>
        </div>

        {
          !loading
          && analyses.length === 0
          && (
            <div className="empty-state">
              No movement analyses yet.
            </div>
          )
        }

        {
          analyses.length > 0
          && (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>
                      File
                    </th>

                    <th>
                      Exercise
                    </th>

                    <th>
                      Reps
                    </th>

                    <th>
                      Status
                    </th>

                    <th>
                      Created
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {
                    analyses.map(
                      (analysis) => (
                        <tr
                          key={analysis.analysis_id}
                        >
                          <td>
                            {
                              analysis.source_filename
                            }
                          </td>

                          <td>
                            {
                              analysis.exercise
                            }
                          </td>

                          <td>
                            {
                              analysis.rep_count
                            }
                          </td>

                          <td>
                            <span className="status-pill">
                              {
                                analysis.status
                              }
                            </span>
                          </td>

                          <td>
                            {
                              new Date(
                                analysis.created_at
                              ).toLocaleString()
                            }
                          </td>
                        </tr>
                      )
                    )
                  }
                </tbody>
              </table>
            </div>
          )
        }
      </section>
    </div>
  );
}