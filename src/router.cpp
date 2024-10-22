#include <cmath>
#include <iostream>
#include <map>
#include <vector>

std::size_t n, m, source, destination;
std::vector<std::pair<double, double>> points; // pairs of (longitude, latitude)
std::vector<std::map<std::size_t, double>> neighbors;

double _convert(double angle)
{
    return angle * M_PI / 180.0;
}

double _distance(
    double lon1, double lat1,
    double lon2, double lat2)
{
    static const double EARTH_RADIUS = 6371.0;

    double dlon = _convert(lon2 - lon1);
    double dlat = _convert(lat2 - lat1);

    double a = std::pow(std::sin(dlat / 2.0), 2) + std::cos(_convert(lat1)) * std::cos(_convert(lat2)) * std::pow(std::sin(dlon / 2.0), 2);
    double c = 2.0 * std::atan2(std::sqrt(a), std::sqrt(1.0 - a));

    return EARTH_RADIUS * c;
}

int main()
{
    long long source_index, destination_index;
    std::cin >> n >> m >> source_index >> destination_index;

    std::map<long long, std::size_t> index_mapping;
    for (std::size_t i = 0; i < n; i++)
    {
        long long index;
        std::cin >> index;
        index_mapping[index] = i;

        double lon, lat;
        std::cin >> lon >> lat;
        points.emplace_back(lon, lat);
    }

    source = index_mapping[source_index];
    destination = index_mapping[destination_index];

    neighbors.resize(n);
    for (std::size_t i = 0; i < m; i++)
    {
        long long u, v;
        std::cin >> u >> v;

        std::size_t u_index = index_mapping[u];
        std::size_t v_index = index_mapping[v];

        double distance = _distance(points[u_index].first, points[u_index].second, points[v_index].first, points[v_index].second);
        neighbors[u_index][v_index] = neighbors[v_index][u_index] = distance;
    }

    return 0;
}
