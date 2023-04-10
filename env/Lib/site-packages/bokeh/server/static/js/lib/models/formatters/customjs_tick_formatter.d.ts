import { TickFormatter } from "./tick_formatter";
import * as p from "../../core/properties";
export declare namespace CustomJSTickFormatter {
    type Attrs = p.AttrsOf<Props>;
    type Props = TickFormatter.Props & {
        args: p.Property<{
            [key: string]: unknown;
        }>;
        code: p.Property<string>;
    };
}
export interface CustomJSTickFormatter extends CustomJSTickFormatter.Attrs {
}
export declare class CustomJSTickFormatter extends TickFormatter {
    properties: CustomJSTickFormatter.Props;
    constructor(attrs?: Partial<CustomJSTickFormatter.Attrs>);
    get names(): string[];
    get values(): unknown[];
    _make_func(): Function;
    doFormat(ticks: number[], _opts: {
        loc: number;
    }): string[];
}
//# sourceMappingURL=customjs_tick_formatter.d.ts.map