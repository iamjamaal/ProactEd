using EquipmentManagement.Services;

namespace EquipmentManagement
{
    public class Startup
    {
        public IConfiguration Configuration { get; }

        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }

        public void ConfigureServices(IServiceCollection services)
        {
            // Add framework services
            services.AddControllers();
            services.AddLogging();

            // Register the Equipment Prediction Service
            // The API URL can be configured in appsettings.json
            var predictionApiUrl = Configuration.GetValue<string>("PredictionService:ApiUrl") ?? "http://localhost:5000";
            services.AddScoped(provider => new EquipmentPredictionService(predictionApiUrl));

            // Optional: Add HTTP client factory for better HTTP client management
            services.AddHttpClient();

            // Add Swagger for API documentation
            services.AddSwaggerGen(c =>
            {
                c.SwaggerDoc("v1", new Microsoft.OpenApi.Models.OpenApiInfo 
                { 
                    Title = "Equipment Management API", 
                    Version = "v1",
                    Description = "Equipment Management System with ML Failure Prediction Integration"
                });
            });

            // Add CORS if needed for web applications
            services.AddCors(options =>
            {
                options.AddDefaultPolicy(builder =>
                {
                    builder.AllowAnyOrigin()
                           .AllowAnyMethod()
                           .AllowAnyHeader();
                });
            });
        }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
                app.UseSwagger();
                app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v1/swagger.json", "Equipment Management API v1"));
            }

            app.UseRouting();
            app.UseCors();
            app.UseAuthorization();

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapControllers();
            });
        }
    }
}
