import { Model } from "../../model";
import { View } from "../../core/view";
import { Indices } from "../../core/types";
import { Context2d } from "../../core/util/canvas";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
import { RendererView } from "../renderers/renderer";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare abstract class MarkingView extends View implements visuals.Renderable {
    model: Marking;
    visuals: Marking.Visuals;
    readonly parent: RendererView;
    size: p.Uniform<number>;
    initialize(): void;
    request_render(): void;
    get canvas(): import("../canvas/canvas").CanvasView;
    set_data(source: ColumnarDataSource, indices: Indices): void;
    abstract render(ctx: Context2d, i: number): void;
}
export declare namespace Marking {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {};
    type Visuals = visuals.Visuals;
}
export interface Marking extends Marking.Attrs {
}
export declare abstract class Marking extends Model {
    properties: Marking.Props;
    __view_type__: MarkingView;
    constructor(attrs?: Partial<Marking.Attrs>);
}
//# sourceMappingURL=marking.d.ts.map