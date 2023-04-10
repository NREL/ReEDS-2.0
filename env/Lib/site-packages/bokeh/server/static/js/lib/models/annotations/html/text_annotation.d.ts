import { Annotation, AnnotationView } from "../annotation";
import * as visuals from "../../../core/visuals";
import * as p from "../../../core/properties";
import { Context2d } from "../../../core/util/canvas";
export declare abstract class TextAnnotationView extends AnnotationView {
    model: TextAnnotation;
    visuals: TextAnnotation.Visuals;
    update_layout(): void;
    protected el: HTMLElement;
    initialize(): void;
    remove(): void;
    connect_signals(): void;
    render(): void;
    protected _paint(ctx: Context2d, text: string, sx: number, sy: number, angle: number): void;
}
export declare namespace TextAnnotation {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props;
    type Visuals = Annotation.Visuals & {
        text: visuals.Text;
        border_line: visuals.Line;
        background_fill: visuals.Fill;
    };
}
export interface TextAnnotation extends TextAnnotation.Attrs {
}
export declare abstract class TextAnnotation extends Annotation {
    properties: TextAnnotation.Props;
    __view_type__: TextAnnotationView;
    constructor(attrs?: Partial<TextAnnotation.Attrs>);
}
//# sourceMappingURL=text_annotation.d.ts.map