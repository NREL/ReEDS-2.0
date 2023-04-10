import { Annotation, AnnotationView } from "./annotation";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { BaseText, BaseTextView } from "../text/base_text";
import { IterViews } from "../../core/build_views";
import { Position } from "../../core/graphics";
import * as mixins from "../../core/property_mixins";
export declare abstract class TextAnnotationView extends AnnotationView {
    model: TextAnnotation;
    visuals: TextAnnotation.Visuals;
    protected _text_view: BaseTextView;
    children(): IterViews;
    lazy_initialize(): Promise<void>;
    protected _init_text(): Promise<void>;
    update_layout(): void;
    connect_signals(): void;
    remove(): void;
    has_finished(): boolean;
    get displayed(): boolean;
    protected _paint(ctx: Context2d, position: Position, angle: number): void;
}
export declare namespace TextAnnotation {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props & {
        text: p.Property<string | BaseText>;
    } & Mixins;
    type Mixins = mixins.Text & mixins.BorderLine & mixins.BackgroundFill;
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