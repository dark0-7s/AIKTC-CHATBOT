import TextBubble from "./renderers/TextBubble";
import TableResponse from "./renderers/TableResponse";
import PredictionCard from "./renderers/PredictionCard";
import MultiPredictionCards from "./renderers/MultiPredictionCards";
import MediaCard from "./renderers/MediaCard";
import FacultyGrid from "./renderers/FacultyGrid";
import ComparisonCards from "./renderers/ComparisonCards";
import ListCards from "./renderers/ListCards";
import StepFlow from "./renderers/StepFlow";
import ContactCard from "./renderers/ContactCard";

const RENDERERS = {
  text: TextBubble,
  table: TableResponse,
  prediction: PredictionCard,
  multi_pred: MultiPredictionCards,
  media_card: MediaCard,
  faculty_grid: FacultyGrid,
  comparison: ComparisonCards,
  list: ListCards,
  steps: StepFlow,
  contact: ContactCard,
};

export default function ResponseRouter({ functionName, args, lang }) {
  const key = functionName?.replace(/^show_/, "") || "text";
  const Renderer = RENDERERS[key] || TextBubble;
  return <Renderer data={args} lang={lang} />;
}