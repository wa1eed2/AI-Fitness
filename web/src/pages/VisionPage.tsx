import {
  ChangeEvent,
  FormEvent,
  useEffect,
  useState
} from "react";

import {
  useAuth
} from "../auth/AuthContext";

import {
  ApiError,
  listVisionAnalyses,
  StoredVisionAnalysis,
  uploadSquatVideo,
  VisionAnalysisSummary
} from "../lib/api";

const MAX_UPLOAD_BYTES = (
  50
  * 1024
  * 1024
);

export function VisionPage() {
  const {
    session
  } = useAuth();

  const [
    file,
    setFile
  ] = useState<File | null>(
    null
  );

  const [
    sampleEvery,
    setSampleEvery
  ] = useState(2);

  const [
    maxAnalyzedFrames,
    setMaxAnalyzedFrames
  ] = useState("");

  const [
    submitting,
    setSubmitting
  ] = useState(false);

  const [
    error,
    setError
  ] = useState<string | null>(
    null
  );

  const [
    latestResult,
    setLatestResult
  ] = useState<StoredVisionAnalysis | null>(
    null
  );

  const [
    history,
    setHistory
  ] = useState<VisionAnalysisSummary[]>(
    []
  );

  async function refreshHistory() {
    if (!session) {
      return;
    }

    const analyses = await listVisionAnalyses(
      session.accessToken,
      10
    );

    setHistory(
      analyses
    );
  }

  useEffect(
    () => {
      if (!session) {
        return;
      }

      void refreshHistory().catch(
        (caughtError) => {
          setError(
            caughtError instanceof ApiError
            ? caughtError.message
            : "Unable to load analysis history."
          );
        }
      );
    },
    [
      session
    ]
  );

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>
  ) {
    const selected = (
      event.target.files?.[
        0
      ]
      ?? null
    );

    setError(
      null
    );

    setLatestResult(
      null
    );

    if (
      selected
      && selected.size
      > MAX_UPLOAD_BYTES
    ) {
      setFile(
        null
      );

      setError(
        "Video must be 50 MB or smaller."
      );

      event.target.value = "";

      return;
    }

    setFile(
      selected
    );
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (
      !session
      || !file
    ) {
      return;
    }

    setSubmitting(
      true
    );

    setError(
      null
    );

    setLatestResult(
      null
    );

    const normalizedMaxFrames = (
      maxAnalyzedFrames.trim()
      ? Number(
          maxAnalyzedFrames
        )
      : null
    );

    if (
      normalizedMaxFrames !== null
      && (
        !Number.isInteger(
          normalizedMaxFrames
        )
        || normalizedMaxFrames < 1
        || normalizedMaxFrames > 10000
      )
    ) {
      setSubmitting(
        false
      );

      setError(
        "Maximum analyzed frames must be between 1 and 10000."
      );

      return;
    }

    try {
      const result = await uploadSquatVideo(
        session.accessToken,
        file,
        sampleEvery,
        normalizedMaxFrames
      );

      setLatestResult(
        result
      );

      await refreshHistory();

    } catch (caughtError) {
      setError(
        caughtError instanceof ApiError
        ? caughtError.message
        : "Video analysis failed."
      );

    } finally {
      setSubmitting(
        false
      );
    }
  }

  const analysis = (
    latestResult?.analysis_result
    ?? null
  );

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <p className="eyebrow">
            Computer vision
          </p>

          <h1>
            Squat video analysis
          </h1>

          <p className="muted">
            Local pose estimation measures
            repetitions and observable 2D
            movement geometry. It does not
            determine medical safety.
          </p>
        </div>
      </header>

      <section className="panel">
        <h2>
          Analyze a video
        </h2>

        <form
          className="form-stack"
          onSubmit={handleSubmit}
        >
          <label className="field">
            <span>
              Video file
            </span>

            <input
              type="file"
              accept=".mp4,.mov,.avi,.mkv,video/mp4,video/quicktime,video/x-msvideo,video/x-matroska"
              required
              onChange={handleFileChange}
            />

            <small>
              Maximum 50 MB. The temporary
              uploaded file is removed after
              analysis.
            </small>
          </label>

          <div className="form-grid">
            <label className="field">
              <span>
                Analyze every Nth frame
              </span>

              <input
                type="number"
                min={1}
                max={30}
                value={sampleEvery}
                onChange={
                  (event) => setSampleEvery(
                    Number(
                      event.target.value
                    )
                  )
                }
              />
            </label>

            <label className="field">
              <span>
                Maximum frames
              </span>

              <input
                type="number"
                min={1}
                max={10000}
                placeholder="Optional"
                value={maxAnalyzedFrames}
                onChange={
                  (event) => setMaxAnalyzedFrames(
                    event.target.value
                  )
                }
              />
            </label>
          </div>

          {file && (
            <div className="file-summary">
              <strong>
                {file.name}
              </strong>

              <span>
                {
                  (
                    file.size
                    / 1024
                    / 1024
                  ).toFixed(
                    2
                  )
                } MB
              </span>
            </div>
          )}

          {error && (
            <div
              className="error-box"
              role="alert"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            className="primary-button"
            disabled={
              submitting
              || !file
            }
          >
            {
              submitting
              ? "Analyzing..."
              : "Analyze squat video"
            }
          </button>
        </form>
      </section>

      {analysis && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">
                Latest result
              </p>

              <h2>
                {
                  latestResult
                    ?.source_filename
                }
              </h2>
            </div>

            <span className="status-pill">
              {analysis.status}
            </span>
          </div>

          <div className="metric-grid">
            <article className="metric-card">
              <span>
                Repetitions
              </span>

              <strong>
                {analysis.rep_count}
              </strong>
            </article>

            <article className="metric-card">
              <span>
                View
              </span>

              <strong className="metric-text">
                {
                  analysis
                    .view_suitability_summary
                    ?.classification
                  ?? "Unavailable"
                }
              </strong>
            </article>

            <article className="metric-card">
              <span>
                Average rep confidence
              </span>

              <strong>
                {
                  analysis
                    .rep_confidence_summary
                    ?.average_rep_confidence
                  !== null
                  && analysis
                    .rep_confidence_summary
                    ?.average_rep_confidence
                  !== undefined
                  ? (
                      analysis
                        .rep_confidence_summary
                        .average_rep_confidence
                      * 100
                    ).toFixed(
                      1
                    ) + "%"
                  : "Unavailable"
                }
              </strong>
            </article>
          </div>

          {
            analysis.repetitions.length > 0
            && (
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>
                        Rep
                      </th>

                      <th>
                        Duration
                      </th>

                      <th>
                        Knee ROM
                      </th>

                      <th>
                        Confidence
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {
                      analysis.repetitions.map(
                        (
                          repetition,
                          index
                        ) => (
                          <tr key={index}>
                            <td>
                              {
                                repetition.repetition_number
                                ?? index + 1
                              }
                            </td>

                            <td>
                              {
                                repetition.duration_seconds
                                !== undefined
                                ? `${repetition.duration_seconds}s`
                                : "—"
                              }
                            </td>

                            <td>
                              {
                                repetition.knee_range_of_motion_degrees
                                !== undefined
                                ? `${repetition.knee_range_of_motion_degrees}°`
                                : "—"
                              }
                            </td>

                            <td>
                              {
                                repetition.confidence_classification
                                ?? "—"
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

          {
            analysis.limitations.length > 0
            && (
              <div className="limitations-box">
                <strong>
                  Measurement limitations
                </strong>

                <ul>
                  {
                    analysis.limitations.map(
                      (
                        limitation,
                        index
                      ) => (
                        <li key={index}>
                          {limitation}
                        </li>
                      )
                    )
                  }
                </ul>
              </div>
            )
          }
        </section>
      )}

      <section className="panel">
        <h2>
          Recent analyses
        </h2>

        {
          history.length === 0
          ? (
            <div className="empty-state">
              No stored analyses yet.
            </div>
          )
          : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>
                      File
                    </th>

                    <th>
                      Reps
                    </th>

                    <th>
                      Status
                    </th>

                    <th>
                      Sampling
                    </th>

                    <th>
                      Created
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {
                    history.map(
                      (item) => (
                        <tr
                          key={item.analysis_id}
                        >
                          <td>
                            {
                              item.source_filename
                            }
                          </td>

                          <td>
                            {
                              item.rep_count
                            }
                          </td>

                          <td>
                            <span className="status-pill">
                              {
                                item.status
                              }
                            </span>
                          </td>

                          <td>
                            Every {
                              item.sample_every_n_frames
                            } frame(s)
                          </td>

                          <td>
                            {
                              new Date(
                                item.created_at
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