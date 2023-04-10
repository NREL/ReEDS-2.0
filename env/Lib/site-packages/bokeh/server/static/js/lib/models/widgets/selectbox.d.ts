import * as p from "../../core/properties";
import { InputWidget, InputWidgetView } from "./input_widget";
export declare class SelectView extends InputWidgetView {
    model: Select;
    input_el: HTMLSelectElement;
    connect_signals(): void;
    private _known_values;
    protected options_el(): HTMLOptionElement[] | HTMLOptGroupElement[];
    render(): void;
    change_input(): void;
    protected _update_value(): void;
}
export declare namespace Select {
    type Attrs = p.AttrsOf<Props>;
    type Props = InputWidget.Props & {
        value: p.Property<string>;
        options: p.Property<(string | [string, string])[] | {
            [key: string]: (string | [string, string])[];
        }>;
    };
}
export interface Select extends Select.Attrs {
}
export declare class Select extends InputWidget {
    properties: Select.Props;
    __view_type__: SelectView;
    constructor(attrs?: Partial<Select.Attrs>);
}
//# sourceMappingURL=selectbox.d.ts.map