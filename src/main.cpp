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

class search_state
{
public:
    const std::size_t index;
    const std::shared_ptr<search_state> parent;
    const double distance_to_src;
    const double lower_bound;

    search_state(
        const std::size_t &index,
        const std::shared_ptr<search_state> &parent,
        const double &distance_to_src,
        const double &lower_bound_to_dest)
        : index(index),
          parent(parent),
          distance_to_src(distance_to_src),
          lower_bound(distance_to_src + lower_bound_to_dest)
    {
    }

    bool operator<(const search_state &other) const
    {
        return lower_bound < other.lower_bound;
    }

    bool operator>(const search_state &other) const
    {
        return lower_bound > other.lower_bound;
    }
};

struct _search_state_comparator
{
    bool operator()(const std::shared_ptr<search_state> &lhs, const std::shared_ptr<search_state> &rhs) const
    {
        return *lhs > *rhs;
    }
};

std::shared_ptr<search_state> a_star(
    std::shared_ptr<search_state> initial_ptr,
    const std::size_t &n,
    const std::size_t &destination,
    const std::vector<std::unordered_map<std::size_t, double>> &neighbors,
    const std::vector<double> &distance_to_dest,
    const std::chrono::time_point<std::chrono::high_resolution_clock, std::chrono::milliseconds> &timeout)
{
    std::vector<double> distances(n, std::numeric_limits<double>::infinity());
    std::priority_queue<std::shared_ptr<search_state>, std::vector<std::shared_ptr<search_state>>, _search_state_comparator> queue;
    queue.push(initial_ptr);

    std::shared_ptr<search_state> result_ptr;
    while (!queue.empty())
    {
        auto pack_ptr = queue.top();
        queue.pop();

        if (pack_ptr->distance_to_src < distances[pack_ptr->index])
        {
            distances[pack_ptr->index] = pack_ptr->distance_to_src;
            if (pack_ptr->index == destination)
            {
                result_ptr = pack_ptr;
                if (std::chrono::high_resolution_clock::now() >= timeout)
                {
                    break;
                }
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
                    auto next_ptr = std::make_shared<search_state>(
                        neighbor,
                        pack_ptr,
                        pack_ptr->distance_to_src + move,
                        distance_to_dest[neighbor]);

                    queue.push(next_ptr);
                }
            }
        }
    }

    return result_ptr;
}

std::shared_ptr<search_state> dfs(
    std::shared_ptr<search_state> initial_ptr,
    const std::size_t &n,
    const std::size_t &destination,
    const std::vector<std::unordered_map<std::size_t, double>> &neighbors,
    const std::vector<double> &distance_to_dest,
    const std::chrono::time_point<std::chrono::high_resolution_clock, std::chrono::milliseconds> &timeout)
{
    std::vector<double> distances(n, std::numeric_limits<double>::infinity());
    std::deque<std::shared_ptr<search_state>> stack = {initial_ptr};

    std::shared_ptr<search_state> result_ptr;
    while (!stack.empty())
    {
        auto pack_ptr = stack.back();
        stack.pop_back();

        if (pack_ptr->distance_to_src < distances[pack_ptr->index])
        {
            distances[pack_ptr->index] = pack_ptr->distance_to_src;
            if (pack_ptr->index == destination)
            {
                result_ptr = pack_ptr;
                if (std::chrono::high_resolution_clock::now() >= timeout)
                {
                    break;
                }
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
                    auto next_ptr = std::make_shared<search_state>(
                        neighbor,
                        pack_ptr,
                        pack_ptr->distance_to_src + move,
                        distance_to_dest[neighbor]);

                    stack.push_front(next_ptr); //Queue, BFS
                }
            }
        }
    }

    return result_ptr;
}

int main()
{
    std::size_t n, m;
    long long source_index, destination_index;
    double timeout;
    std::cin >> n >> m >> source_index >> destination_index >> timeout;

    // Pair of longitude and latitude
    std::vector<std::pair<double, double>> points;

    // Map from original index to 0-based index
    std::unordered_map<long long, std::size_t> index_unordered_mapping;

    // Map from 0-based index to original index
    std::vector<long long> reverse_index_unordered_mapping;
    for (std::size_t i = 0; i < n; i++)
    {
        long long index;
        std::cin >> index;
        index_unordered_mapping[index] = i;
        reverse_index_unordered_mapping.push_back(index);

        double lon, lat;
        std::cin >> lon >> lat;
        points.emplace_back(lon, lat);
    }

    std::size_t source = index_unordered_mapping[source_index], destination = index_unordered_mapping[destination_index];

    const auto metric = [&points](std::size_t i, std::size_t j)
    {
        return haversine(points[i].first, points[i].second, points[j].first, points[j].second);
    };

    std::vector<std::unordered_map<std::size_t, double>> neighbors(n);
    for (std::size_t i = 0; i < m; i++)
    {
        long long u, v;
        std::cin >> u >> v;

        std::size_t u_index = index_unordered_mapping[u];
        std::size_t v_index = index_unordered_mapping[v];

        neighbors[u_index][v_index] = metric(u_index, v_index);
    }

    std::vector<double> distance_to_dest(n);
    for (std::size_t i = 0; i < n; i++)
    {
        distance_to_dest[i] = metric(i, destination);
    }

    auto initial_ptr = std::make_shared<search_state>(
        source,
        nullptr,
        0.0,
        metric(source, destination));

    std::shared_ptr<search_state> result_ptr;
    const auto time_limit = std::chrono::time_point_cast<std::chrono::milliseconds>(
        std::chrono::high_resolution_clock::now() + std::chrono::milliseconds(static_cast<std::size_t>(1000.0 * timeout)));

#if defined(A_STAR)
    result_ptr = a_star(initial_ptr, n, destination, neighbors, distance_to_dest, time_limit);
#elif defined(DFS)
    result_ptr = dfs(initial_ptr, n, destination, neighbors, distance_to_dest, time_limit);
#else
    static_assert(false, "No search algorithm specified");
#endif

    std::cerr << "Found route with distance = " << result_ptr->distance_to_src << " km (explored " << n << " vertices and " << m << " edges)." << std::endl;

    std::vector<std::size_t> result;
    while (result_ptr != nullptr)
    {
        result.push_back(result_ptr->index);
        result_ptr = result_ptr->parent;
    }

    std::reverse(result.begin(), result.end());
    for (auto &index : result)
    {
        std::cout << reverse_index_unordered_mapping[index] << " ";
    }
    std::cout << std::endl;

    return 0;
}
