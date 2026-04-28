import { useNavigate, useParams } from "react-router-dom";

import { PageHeader } from "@/components/Common/PageHeader";
import { UploadWizard } from "@/components/Projects/UploadWizard";

export const ProjectUploadPage = () => {
  const { projectId = "" } = useParams();
  const navigate = useNavigate();

  return (
    <div className="space-y-8">
      <PageHeader
        title="Run a new audit"
        subtitle="Upload a dataset, configure protected attributes, optionally attach a trained model, and launch an asynchronous fairness review."
      />
      <UploadWizard projectId={projectId} onCompleted={(runId) => navigate(`/runs/${runId}`)} />
    </div>
  );
};

