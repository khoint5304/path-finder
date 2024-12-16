#include "standard.hpp"

/// @brief Convert angle from degrees to radians
double convert(double angle)
{
    return angle * M_PI / 180.0;
}

/// @brief Calculate the distance between two points on Earth using the Haversine formula
/// @see https://stackoverflow.com/a/26447032
double haversine(double lon1, double lat1, double lon2, double lat2)
{
    static const double EARTH_RADIUS = 6371.0;

    double dlon = convert(lon2 - lon1);
    double dlat = convert(lat2 - lat1);

    double a = std::pow(std::sin(dlat / 2.0), 2) + std::cos(convert(lat1)) * std::cos(convert(lat2)) * std::pow(std::sin(dlon / 2.0), 2);
    double b = 2.0 * std::asin(std::sqrt(a));

    return EARTH_RADIUS * b;
}

class search_pack
{
public:
    const std::size_t index;
    const std::shared_ptr<search_pack> parent;
    const double distance_to_src;
    const double lower_bound_to_dest;
    const double lower_bound;

    search_pack(
        std::size_t index,
        std::shared_ptr<search_pack> parent,
        double distance_to_src,
        double lower_bound_to_dest)
        : index(index),
          parent(parent),
          distance_to_src(distance_to_src),
          lower_bound_to_dest(lower_bound_to_dest),
          lower_bound(distance_to_src + lower_bound_to_dest)
    {
    }

    bool operator<(const search_pack &other) const
    {
        return lower_bound < other.lower_bound;
    }
};

int main()
{
    std::size_t n, m;
    long long source_index, destination_index;
    std::cin >> n >> m >> source_index >> destination_index;

    // Pair of longitude and latitude
    std::vector<std::pair<double, double>> points;

    // Map from original index to 0-based index
    std::map<long long, std::size_t> index_mapping;

    // Map from 0-based index to original index
    std::vector<long long> reverse_index_mapping;
    for (std::size_t i = 0; i < n; i++)
    {
        long long index;
        std::cin >> index;
        index_mapping[index] = i;
        reverse_index_mapping.push_back(index);

        double lon, lat;
        std::cin >> lon >> lat;
        points.emplace_back(lon, lat);
    }

    std::size_t source = index_mapping[source_index], destination = index_mapping[destination_index];
    std::cerr << "Source: " << points[source] << std::endl;
    std::cerr << "Destination: " << points[destination] << std::endl;

    const auto metric = [&points](std::size_t i, std::size_t j)
    {
        return haversine(points[i].first, points[i].second, points[j].first, points[j].second);
    };

    std::vector<std::map<std::size_t, double>> neighbors(n);
    for (std::size_t i = 0; i < m; i++)
    {
        long long u, v;
        std::cin >> u >> v;

        std::size_t u_index = index_mapping[u];
        std::size_t v_index = index_mapping[v];

        neighbors[u_index][v_index] = metric(u_index, v_index);
    }

    std::vector<double> distances(n, std::numeric_limits<double>::infinity());
    std::shared_ptr<search_pack> result_ptr;

    auto initial_ptr = std::make_shared<search_pack>(
        source,
        nullptr,
        0.0,
        metric(source, destination));

#ifdef A_STAR
    std::set<std::shared_ptr<search_pack>> queue;
    queue.insert(initial_ptr);
#else
    std::deque<std::shared_ptr<search_pack>> queue;
    queue.push_back(initial_ptr);
#endif

    while (!queue.empty())
    {
#ifdef A_STAR
        auto pack_ptr = *queue.begin();
        queue.erase(queue.begin());
#else
        auto pack_ptr = queue.front();
        queue.pop_front();
#endif

        if (pack_ptr->distance_to_src < distances[pack_ptr->index])
        {
            distances[pack_ptr->index] = pack_ptr->distance_to_src;
            if (pack_ptr->index == destination)
            {
                result_ptr = pack_ptr;
            }
            else
            {
                // Branch-and-bound elimination
                if (result_ptr != nullptr && pack_ptr->lower_bound > result_ptr->distance_to_src)
                {
                    continue;
                }

                for (auto &[neighbor, move] : neighbors[pack_ptr->index])
                {
                    auto next_ptr = std::make_shared<search_pack>(
                        neighbor,
                        pack_ptr,
                        pack_ptr->distance_to_src + move,
                        metric(neighbor, destination));

#ifdef A_STAR
                    queue.insert(next_ptr);
#else
                    queue.push_back(next_ptr);
#endif
                }
            }
        }
    }

    std::cerr << "Found route with distance = " << result_ptr->distance_to_src << " km" << std::endl;

    std::vector<std::size_t> result;
    while (result_ptr != nullptr)
    {
        result.push_back(result_ptr->index);
        result_ptr = result_ptr->parent;
    }

    std::reverse(result.begin(), result.end());
    for (auto &index : result)
    {
        std::cout << reverse_index_mapping[index] << " ";
    }
    std::cout << std::endl;

    return 0;
}
