import { useQuery } from '@tanstack/react-query'
import { settingsApi } from '../../api/settings'
import Spinner from '../../components/common/Spinner'
import Badge from '../../components/common/Badge'

export default function QualityProfilesSettings() {
  const { data: profiles = [], isLoading } = useQuery({
    queryKey: ['quality-profiles'],
    queryFn: settingsApi.listQualityProfiles,
  })
  const { data: langProfiles = [] } = useQuery({
    queryKey: ['language-profiles'],
    queryFn: settingsApi.listLanguageProfiles,
  })

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h3 className="font-semibold text-gray-200 mb-3">Quality Profiles</h3>
        <div className="space-y-3">
          {profiles.map((p) => (
            <div key={p.id} className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="font-medium text-gray-200">{p.name}</span>
                {p.is_default && <Badge variant="info">Default</Badge>}
              </div>
              <div className="flex flex-wrap gap-2">
                {p.items.map((item) => (
                  <Badge key={item.id} variant={item.allowed ? 'success' : 'muted'}>
                    {item.quality}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="font-semibold text-gray-200 mb-3">Language Profiles</h3>
        <div className="space-y-3">
          {langProfiles.map((p) => (
            <div key={p.id} className="card p-4">
              <span className="font-medium text-gray-200 block mb-2">{p.name}</span>
              <div className="flex gap-2">
                {p.languages.map((lang) => (
                  <Badge key={lang} variant="info">{lang.toUpperCase()}</Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
