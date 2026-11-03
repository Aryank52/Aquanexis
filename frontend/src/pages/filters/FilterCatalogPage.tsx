import { useState } from 'react';
import {
  Plus,
  Search,
  Filter as FilterIcon,
  Edit,
  Trash2,
  Package,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Input } from '@components/ui/Input';
import { Skeleton, QueryError, EmptyState } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import {
  useFilterCatalog,
  useCreateFilter,
  useUpdateFilter,
  useCheckCompatibility,
} from '@/hooks/useMaintenance';
import type {
  FilterCatalogResponse,
  FilterCategory,
  CompatibilityResult,
  FilterCatalogCreate,
  FilterCatalogUpdate,
} from '@/types/api';

const categoryLabels: Record<FilterCategory, string> = {
  SEDIMENT: 'Sediment',
  CARBON: 'Carbon',
  RO_MEMBRANE: 'RO Membrane',
  POST_CARBON: 'Post Carbon',
  UV: 'UV',
  MINERALIZATION: 'Mineralization',
  OTHER: 'Other',
};

interface FilterFormData {
  filter_identifier?: string;
  manufacturer?: string;
  product_name?: string;
  category?: FilterCategory;
  purifier_compatibility?: string[];
  stage_position?: number;
  specifications?: Record<string, unknown>;
  connector_details?: string | null;
  dimensions_mm?: Record<string, number>;
  rated_service_interval_days?: number;
  rated_usage_volume_liters?: number;
  installation_requirements?: string;
  maintenance_instructions?: string;
  datasheet_reference?: string;
  is_active?: boolean;
}

function compatIcon(result: CompatibilityResult) {
  switch (result) {
    case 'COMPATIBLE':
      return <CheckCircle className="h-4 w-4 text-success" />;
    case 'INCOMPATIBLE':
      return <AlertTriangle className="h-4 w-4 text-critical" />;
    default:
      return <Package className="h-4 w-4 text-text-muted" />;
  }
}

export function FilterCatalogPage() {
  const [showForm, setShowForm] = useState<FilterCatalogResponse | null>(null);
  const [isAddingNew, setIsAddingNew] = useState(false);
  const [formData, setFormData] = useState<FilterFormData>({});
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [compatCheck, setCompatCheck] = useState<{
    result: CompatibilityResult;
    details: string;
  } | null>(null);
  const [compatForm, setCompatForm] = useState({
    purifier_model: '',
    filter_id: '',
    stage_position: 1,
  });

  const catalog = useFilterCatalog({
    category: filterCategory === 'all' ? undefined : (filterCategory as FilterCategory),
  });
  const createFilter = useCreateFilter();
  const updateFilter = useUpdateFilter();
  const checkCompat = useCheckCompatibility();

  if (catalog.isError) {
    return (
      <QueryError
        message={(catalog.error as Error)?.message ?? 'Failed to load filter catalog'}
        onRetry={catalog.refetch}
      />
    );
  }

  const filteredCatalog =
    catalog.data?.filter(
      item =>
        item.product_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.manufacturer.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.filter_identifier.toLowerCase().includes(searchQuery.toLowerCase())
    ) ?? [];

  const handleSubmit = () => {
    if (showForm) {
      updateFilter.mutate(
        { filterId: showForm.id, data: formData as FilterCatalogUpdate },
        {
          onSuccess: () => {
            setShowForm(null);
            setIsAddingNew(false);
            setFormData({});
            catalog.refetch();
          },
        }
      );
    } else {
      createFilter.mutate(formData as FilterCatalogCreate, {
        onSuccess: () => {
          setShowForm(null);
          setIsAddingNew(false);
          setFormData({});
          catalog.refetch();
        },
      });
    }
  };

  const handleCompatCheck = () => {
    checkCompat.mutate(compatForm, {
      onSuccess: result => {
        setCompatCheck({ result: result.result, details: JSON.stringify(result.details, null, 2) });
      },
    });
  };

  const openNewForm = () => {
    setShowForm(null);
    setIsAddingNew(true);
    setFormData({});
  };

  const openEditForm = (filter: FilterCatalogResponse) => {
    setIsAddingNew(false);
    setShowForm(filter);
    setFormData({
      filter_identifier: filter.filter_identifier,
      manufacturer: filter.manufacturer,
      product_name: filter.product_name,
      category: filter.category,
      purifier_compatibility: filter.purifier_compatibility,
      stage_position: filter.stage_position,
      specifications: filter.specifications,
      connector_details: filter.connector_details ?? undefined,
      dimensions_mm: filter.dimensions_mm ?? undefined,
      rated_service_interval_days: filter.rated_service_interval_days ?? undefined,
      rated_usage_volume_liters: filter.rated_usage_volume_liters ?? undefined,
      installation_requirements: filter.installation_requirements ?? undefined,
      maintenance_instructions: filter.maintenance_instructions ?? undefined,
      datasheet_reference: filter.datasheet_reference ?? undefined,
      is_active: filter.is_active,
    });
  };

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-text-primary text-h1 font-semibold">Filter Catalog</h1>
          <p className="mt-1 text-body-sm text-text-secondary">
            Manage filter specifications and compatibility
          </p>
        </div>
        <Button onClick={openNewForm}>
          <Plus className="mr-1 h-4 w-4" /> Add Filter
        </Button>
      </div>

      {/* Filters & Search */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative min-w-[200px] flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
              <Input
                placeholder="Search filters..."
                value={searchQuery}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setSearchQuery(e.target.value)
                }
                className="pl-10"
              />
            </div>
            <select
              className="input w-48 text-body-sm"
              value={filterCategory}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                setFilterCategory(e.target.value)
              }
              aria-label="Filter by category"
            >
              <option value="all">All Categories</option>
              <option value="SEDIMENT">Sediment</option>
              <option value="CARBON">Carbon</option>
              <option value="RO_MEMBRANE">RO Membrane</option>
              <option value="POST_CARBON">Post Carbon</option>
              <option value="UV">UV</option>
              <option value="MINERALIZATION">Mineralization</option>
              <option value="OTHER">Other</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Compatibility Check */}
      <Card className="border-info bg-info/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FilterIcon className="h-4 w-4 text-info" /> Compatibility Check
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div>
              <label className="label">Purifier Model</label>
              <Input
                value={compatForm.purifier_model}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setCompatForm(prev => ({ ...prev, purifier_model: e.target.value }))
                }
                placeholder="e.g., AQX-500"
              />
            </div>
            <div>
              <label className="label">Filter</label>
              <select
                className="input text-body-sm"
                value={compatForm.filter_id}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                  setCompatForm(prev => ({ ...prev, filter_id: e.target.value }))
                }
              >
                <option value="">Select filter</option>
                {catalog.data?.map(f => (
                  <option key={f.id} value={f.id}>
                    {f.product_name} ({f.filter_identifier})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Stage Position</label>
              <Input
                type="number"
                min="1"
                value={compatForm.stage_position}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setCompatForm(prev => ({
                    ...prev,
                    stage_position: parseInt(e.target.value) || 1,
                  }))
                }
              />
            </div>
          </div>
          <Button
            onClick={handleCompatCheck}
            disabled={checkCompat.isPending || !compatForm.filter_id || !compatForm.purifier_model}
          >
            {checkCompat.isPending ? 'Checking…' : 'Check Compatibility'}
          </Button>
          {compatCheck && (
            <div className="border-subtle flex items-center gap-3 rounded-button border bg-surface p-3">
              {compatIcon(compatCheck.result)}
              <div>
                <div className="text-body-sm font-medium">
                  {compatCheck.result === 'COMPATIBLE'
                    ? 'Compatible'
                    : compatCheck.result === 'INCOMPATIBLE'
                      ? 'Incompatible'
                      : 'Unknown'}
                </div>
                <div className="text-caption text-text-muted">{compatCheck.details}</div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Filter Catalog Table */}
      <Card>
        <CardHeader>
          <CardTitle>Filters ({catalog.isLoading ? '…' : filteredCatalog.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {catalog.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full rounded" />
              ))}
            </div>
          ) : filteredCatalog.length === 0 ? (
            <EmptyState title="No filters found" description="Add a new filter to get started" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-body-sm">
                <thead>
                  <tr className="border-subtle border-b text-left text-text-secondary">
                    <th className="px-3 py-2 font-medium">Identifier</th>
                    <th className="px-3 py-2 font-medium">Product</th>
                    <th className="px-3 py-2 font-medium">Manufacturer</th>
                    <th className="px-3 py-2 font-medium">Category</th>
                    <th className="px-3 py-2 font-medium">Stage</th>
                    <th className="px-3 py-2 font-medium">Service Interval</th>
                    <th className="px-3 py-2 font-medium">Status</th>
                    <th className="sr-only px-3 py-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-subtle divide-y">
                  {filteredCatalog.map(filter => (
                    <tr key={filter.id} className="transition-colors hover:bg-hover">
                      <td className="text-text-primary px-3 py-2 font-mono">
                        {filter.filter_identifier}
                      </td>
                      <td className="text-text-primary px-3 py-2 font-medium">
                        {filter.product_name}
                      </td>
                      <td className="px-3 py-2 text-text-secondary">{filter.manufacturer}</td>
                      <td className="px-3 py-2">
                        <Badge variant="default">{categoryLabels[filter.category]}</Badge>
                      </td>
                      <td className="px-3 py-2 text-text-secondary">{filter.stage_position}</td>
                      <td className="px-3 py-2 text-text-muted">
                        {filter.rated_service_interval_days
                          ? `${filter.rated_service_interval_days} days`
                          : '—'}
                        {filter.rated_usage_volume_liters
                          ? ` / ${filter.rated_usage_volume_liters}L`
                          : ''}
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant={filter.is_active ? 'success' : 'default'}>
                          {filter.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </td>
                      <td className="px-3 py-2">
                        <Button variant="ghost" size="sm" onClick={() => openEditForm(filter)}>
                          Edit
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Form Modal */}
      {(showForm !== null || isAddingNew) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-card bg-elevated p-6 shadow-elevated">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-h2 font-semibold">{showForm ? 'Edit Filter' : 'Add Filter'}</h2>
              <button
                onClick={() => {
                  setShowForm(null);
                  setIsAddingNew(false);
                  setFormData({});
                }}
                className="rounded-button p-1 hover:bg-hover"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Filter Identifier *</label>
                  <Input
                    value={formData.filter_identifier ?? ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setFormData(prev => ({ ...prev, filter_identifier: e.target.value }))
                    }
                    required
                  />
                </div>
                <div>
                  <label className="label">Manufacturer *</label>
                  <Input
                    value={formData.manufacturer ?? ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setFormData(prev => ({ ...prev, manufacturer: e.target.value }))
                    }
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Product Name *</label>
                <Input
                  value={formData.product_name ?? ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormData(prev => ({ ...prev, product_name: e.target.value }))
                  }
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Category *</label>
                  <select
                    className="input text-body-sm"
                    value={formData.category ?? ''}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                      setFormData(prev => ({ ...prev, category: e.target.value as FilterCategory }))
                    }
                    required
                  >
                    <option value="">Select category</option>
                    <option value="SEDIMENT">Sediment</option>
                    <option value="CARBON">Carbon</option>
                    <option value="RO_MEMBRANE">RO Membrane</option>
                    <option value="POST_CARBON">Post Carbon</option>
                    <option value="UV">UV</option>
                    <option value="MINERALIZATION">Mineralization</option>
                    <option value="OTHER">Other</option>
                  </select>
                </div>
                <div>
                  <label className="label">Stage Position *</label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.stage_position ?? ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setFormData(prev => ({
                        ...prev,
                        stage_position: parseInt(e.target.value) || 1,
                      }))
                    }
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Purifier Compatibility (comma-separated)</label>
                <Input
                  value={formData.purifier_compatibility?.join(', ') ?? ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setFormData(prev => ({
                      ...prev,
                      purifier_compatibility: e.target.value
                        .split(',')
                        .map(s => s.trim())
                        .filter(Boolean),
                    }))
                  }
                  placeholder="e.g., AQX-500, AQX-300"
                />
              </div>

              <div>
                <label className="label">Specifications (JSON)</label>
                <textarea
                  className="input font-mono text-caption"
                  rows={3}
                  value={JSON.stringify(formData.specifications ?? {}, null, 2)}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => {
                    try {
                      setFormData(prev => ({
                        ...prev,
                        specifications: JSON.parse(e.target.value),
                      }));
                    } catch {}
                  }}
                  placeholder='{"pore_size_micron": 5, "material": "polypropylene"}'
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Service Interval (days)</label>
                  <Input
                    type="number"
                    value={formData.rated_service_interval_days ?? ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setFormData(prev => ({
                        ...prev,
                        rated_service_interval_days: parseInt(e.target.value) || undefined,
                      }))
                    }
                  />
                </div>
                <div>
                  <label className="label">Usage Volume (liters)</label>
                  <Input
                    type="number"
                    step="any"
                    value={formData.rated_usage_volume_liters ?? ''}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setFormData(prev => ({
                        ...prev,
                        rated_usage_volume_liters: parseFloat(e.target.value) || undefined,
                      }))
                    }
                  />
                </div>
              </div>

              <div className="border-subtle flex gap-2 border-t pt-4">
                <Button
                  variant="primary"
                  className="flex-1"
                  onClick={handleSubmit}
                  disabled={createFilter.isPending || updateFilter.isPending}
                >
                  {createFilter.isPending || updateFilter.isPending
                    ? 'Saving…'
                    : showForm
                      ? 'Update'
                      : 'Create'}
                </Button>
                <Button
                  variant="ghost"
                  className="flex-1"
                  onClick={() => {
                    setShowForm(null);
                    setIsAddingNew(false);
                    setFormData({});
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
