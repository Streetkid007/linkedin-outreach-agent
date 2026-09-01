def get_field(fid): .fields[] | select(.id == fid) | .value;
def get_field_safe(fid): ([ .fields[] | select(.id == fid) | .value ] | first) // null;

.data[] |
{
  list_entry_id: .id,
  entity_id: .entity.id,
  company_name: .entity.name,
  domain: .entity.domain,
  createdAt: .createdAt,
  founder_linkedin_verified: (get_field_safe("field-5875046")),
  founder_linkedin_enriched: (
    [ .fields[] | select(.id == "affinity-data-linkedin-profile-founders-ceos") | .value[]? |
      if type == "object" then (.link // .url // .text // .["filterable-text"] // tostring)
      else tostring
      end
    ] | if length == 0 then null else . end
  ),
  company_description: (get_field_safe("affinity-data-description")),
  year_founded: (get_field_safe("affinity-data-year-founded")),
  industry_clover: (get_field_safe("field-5685231")),
  location_clover: (get_field_safe("field-5685235")),
  company_linkedin_url: (get_field_safe("affinity-data-linkedin-url"))
}
