class LookCommand:
    def __init__(self):
        self.trigger = "look"

    def parse(self, raw: str) -> dict[str, str]:
        """
        >>> cmd = LookCommand()
        >>> cmd.parse("look")
        {}
        >>> cmd.parse("look at box")
        {'at': 'box'}
        >>> cmd.parse('''look at "Jasper's suitcase"''')
        {'at': "Jasper's suitcase"}
        >>> cmd.parse('look in box')
        {'in': 'box'}
        >>> cmd.parse('look in "large suitcase"')
        {'in': 'large suitcase'}
        """
        raw = raw.replace(self.trigger, "").strip()
        parsed = dict()
        if len(raw) == 0:
            return parsed

        segments = raw.split(" ")
        current_idx = 0
        grouped_segments = []
        while current_idx < len(segments):
            current_segment = segments[current_idx]
            if current_segment.startswith('"'):
                look_idx = current_idx
                end_idx = None
                while look_idx < len(segments):
                    look_segment = segments[look_idx]
                    if look_segment.endswith('"'):
                        end_idx = look_idx
                        break
                    else:
                        look_idx += 1
                if end_idx is None:
                    raise ValueError("Unmatched quote found!")
                grouped_segments.append(" ".join(segments[current_idx:end_idx+1]).strip('"'))
                current_idx = end_idx
            else:
                grouped_segments.append(current_segment)
            current_idx += 1
        for idx, segment in enumerate(grouped_segments):
            if segment in ("at", "in"):
                parsed[segment] = grouped_segments[idx + 1]
        return parsed
