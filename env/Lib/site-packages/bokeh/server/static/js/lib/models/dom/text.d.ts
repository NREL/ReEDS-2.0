import { DOMNode, DOMNodeView } from "./dom_node";
import * as p from "../../core/properties";
export declare class TextView extends DOMNodeView {
    model: Text;
    el: globalThis.Text;
    render(): void;
    protected _createElement(): globalThis.Text;
}
export declare namespace Text {
    type Attrs = p.AttrsOf<Props>;
    type Props = DOMNode.Props & {
        content: p.Property<string>;
    };
}
export interface Text extends Text.Attrs {
}
export declare class Text extends DOMNode {
    properties: Text.Props;
    __view_type__: TextView;
    constructor(attrs?: Partial<Text.Attrs>);
}
//# sourceMappingURL=text.d.ts.map