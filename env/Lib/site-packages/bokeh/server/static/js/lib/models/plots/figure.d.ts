import { Plot, PlotView } from "./plot";
import { SerializableState } from "../../core/view";
import * as p from "../../core/properties";
export declare class FigureView extends PlotView {
    model: Figure;
    serializable_state(): SerializableState;
}
export declare namespace Figure {
    type Attrs = p.AttrsOf<Props>;
    type Props = Plot.Props;
}
export interface Figure extends Figure.Attrs {
}
export declare class Figure extends Plot {
    properties: Figure.Props;
    __view_type__: FigureView;
    constructor(attrs?: Partial<Figure.Attrs>);
}
//# sourceMappingURL=figure.d.ts.map