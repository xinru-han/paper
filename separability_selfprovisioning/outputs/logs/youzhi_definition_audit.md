# Youzhi Definition Audit

Generated at: 2026-07-06 14:26:59

## Finding

- Raw labels contain aggregate `youzhi` consumption/source variables: TRUE.
- Raw labels contain oilseed production module variables (`youliao_shengchan`): TRUE.
- The food-category documentation defines `youzhi` as `油脂类`.
- The available labels do not clearly state whether the strong `youzhi` result reflects oil crops, home-produced edible oil, self-retained oilseeds, purchased oils with self-production source, or a mixture.

## Decision

- Keep `youzhi` as the aggregate oils category in revised models.
- Human review required before making strong substantive claims about the oil category.
