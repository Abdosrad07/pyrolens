/**
 * HarmonizationNew - View for creating a new experiment
 */
import { useState } from "react";
import { createExperiment } from "../data.js";
import ExperimentForm from "../components/ExperimentForm.jsx";
import LoadingState from "../components/LoadingState.jsx";
import ErrorState from "../components/ErrorState.jsx";

export default function HarmonizationNew() {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [jobId, setJobId] = useState(null);

  const handleSubmit = async (formData) => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await createExperiment(formData);
      setJobId(result.job_id);
      window.location.hash = `harmonization-${result.job_id}`;
    } catch (err) {
      setError(err);
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    window.location.hash = "harmonization";
  };

  if (submitting) {
    return (
      <div>
        <h2 className="page-title">Nouvelle expérience</h2>
        <p className="page-sub">
          Configurez les paramètres de l'expérience d'harmonisation.
        </p>
        <div className="panel">
          <LoadingState message="Création de l'expérience en cours…" />
        </div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="page-title">Nouvelle expérience</h2>
      <p className="page-sub">
        Configurez les paramètres de l'expérience d'harmonisation.
      </p>
      {error && <ErrorState error={error} onRetry={() => setError(null)} />}
      <ExperimentForm onSubmit={handleSubmit} onCancel={handleCancel} />
    </div>
  );
}
