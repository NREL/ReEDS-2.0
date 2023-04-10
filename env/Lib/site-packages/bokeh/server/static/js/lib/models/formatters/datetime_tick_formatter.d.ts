import { ContextWhich, Location } from "../../core/enums";
import * as p from "../../core/properties";
import { TickFormatter } from "./tick_formatter";
export type ResolutionType = "microseconds" | "milliseconds" | "seconds" | "minsec" | "minutes" | "hourmin" | "hours" | "days" | "months" | "years";
export declare const resolution_order: ResolutionType[];
export declare const tm_index_for_resolution: Map<ResolutionType, number>;
export declare function _get_resolution(resolution_secs: number, span_secs: number): ResolutionType;
export declare function _mktime(t: number): number[];
export declare function _strftime(t: number, format: string): string;
export declare function _us(t: number): number;
export declare namespace DatetimeTickFormatter {
    type Attrs = p.AttrsOf<Props>;
    type Props = TickFormatter.Props & {
        microseconds: p.Property<string>;
        milliseconds: p.Property<string>;
        seconds: p.Property<string>;
        minsec: p.Property<string>;
        minutes: p.Property<string>;
        hourmin: p.Property<string>;
        hours: p.Property<string>;
        days: p.Property<string>;
        months: p.Property<string>;
        years: p.Property<string>;
        strip_leading_zeros: p.Property<boolean>;
        context: p.Property<string | DatetimeTickFormatter | null>;
        context_which: p.Property<ContextWhich>;
        context_location: p.Property<Location>;
    };
}
export interface DatetimeTickFormatter extends DatetimeTickFormatter.Attrs {
}
export declare class DatetimeTickFormatter extends TickFormatter {
    properties: DatetimeTickFormatter.Props;
    constructor(attrs?: Partial<DatetimeTickFormatter.Attrs>);
    doFormat(ticks: number[], _opts: {
        loc: number;
    }, _resolution?: ResolutionType): string[];
    _compute_label(t: number, resolution: ResolutionType): string;
    _add_context(tick: number, label: string, i: number, N: number, resolution: ResolutionType): string;
}
//# sourceMappingURL=datetime_tick_formatter.d.ts.map