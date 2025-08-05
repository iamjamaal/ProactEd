import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set style for better visualizations
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_and_analyze_dataset(filepath='knust_classroom_equipment_dataset.csv'):
    """Load and perform comprehensive analysis of the classroom equipment dataset"""
    
    print("=" * 60)
    print("KNUST CLASSROOM EQUIPMENT PREDICTIVE MAINTENANCE DATASET")
    print("=" * 60)
    
    # Load dataset
    df = pd.read_csv(filepath)
    print(f"Dataset loaded successfully!")
    print(f"Shape: {df.shape[0]} records, {df.shape[1]} features")
    
    # Basic information
    print("\n" + "="*50)
    print("1. BASIC DATASET INFORMATION")
    print("="*50)
    
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    print(f"Date range: {df['installation_date'].min()} to {df['installation_date'].max()}")
    
    # Missing values check
    missing_values = df.isnull().sum()
    if missing_values.sum() > 0:
        print(f"\nMissing values found: {missing_values[missing_values > 0]}")
    else:
        print("\nNo missing values found ✓")
    
    # Equipment distribution
    print("\n" + "="*50)
    print("2. EQUIPMENT DISTRIBUTION")
    print("="*50)
    
    equipment_stats = df.groupby('equipment_type').agg({
        'equipment_id': 'count',
        'age_months': 'mean',
        'failure_probability': 'mean',
        'daily_usage_hours': 'mean'
    }).round(2)
    equipment_stats.columns = ['Count', 'Avg_Age_Months', 'Avg_Failure_Prob', 'Avg_Daily_Usage']
    print(equipment_stats)
    
    # Academic calendar impact
    print("\n" + "="*50)
    print("3. ACADEMIC CALENDAR IMPACT")
    print("="*50)
    
    academic_impact = df.groupby(['week_of_year', 'is_exam_period']).agg({
        'daily_usage_hours': 'mean',
        'failure_probability': 'mean'
    }).round(3)
    
    exam_weeks = df[df['is_exam_period'] == True]
    regular_weeks = df[df['is_exam_period'] == False]
    
    print(f"Average usage during exam periods: {exam_weeks['daily_usage_hours'].mean():.2f} hours/day")
    print(f"Average usage during regular periods: {regular_weeks['daily_usage_hours'].mean():.2f} hours/day")
    print(f"Failure probability during exams: {exam_weeks['failure_probability'].mean():.3f}")
    print(f"Failure probability during regular periods: {regular_weeks['failure_probability'].mean():.3f}")
    
    # Climate impact analysis
    print("\n" + "="*50)
    print("4. CLIMATE IMPACT ANALYSIS")
    print("="*50)
    
    # Define seasons based on week_of_year
    def get_season(week):
        if week in list(range(1, 9)) + list(range(49, 53)):
            return 'Harmattan'
        elif week in list(range(17, 43)):
            return 'Rainy'
        else:
            return 'Dry'
    
    df['season'] = df['week_of_year'].apply(get_season)
    
    climate_impact = df.groupby('season').agg({
        'dust_factor': 'mean',
        'humidity': 'mean',
        'operating_temperature': 'mean',
        'failure_probability': 'mean'
    }).round(3)
    print(climate_impact)
    
    # Maintenance urgency distribution
    print("\n" + "="*50)
    print("5. MAINTENANCE URGENCY ANALYSIS")
    print("="*50)
    
    urgency_stats = df.groupby(['equipment_type', 'maintenance_urgency']).size().unstack(fill_value=0)
    print(urgency_stats)
    
    # Critical equipment identification
    critical_equipment = df[df['maintenance_urgency'] == 'critical']
    print(f"\nCritical equipment count: {len(critical_equipment)} ({len(critical_equipment)/len(df)*100:.1f}%)")
    
    if len(critical_equipment) > 0:
        print("Critical equipment characteristics:")
        critical_stats = critical_equipment.groupby('equipment_type').agg({
            'age_months': 'mean',
            'degradation_score': 'mean',
            'last_maintenance_days': 'mean',
            'operating_temperature': 'mean'
        }).round(2)
        print(critical_stats)
    
    # Feature correlations
    print("\n" + "="*50)
    print("6. KEY FEATURE CORRELATIONS WITH FAILURE PROBABILITY")
    print("="*50)
    
    numeric_features = ['age_months', 'daily_usage_hours', 'total_usage_hours', 
                       'last_maintenance_days', 'degradation_score', 'operating_temperature',
                       'power_consumption', 'performance_score', 'vibration_level', 
                       'dust_accumulation']
    
    correlations = df[numeric_features + ['failure_probability']].corr()['failure_probability'].drop('failure_probability').sort_values(key=abs, ascending=False)
    
    print("Top correlations with failure probability:")
    for feature, corr in correlations.head(8).items():
        direction = "↑" if corr > 0 else "↓"
        print(f"{feature:25s}: {corr:6.3f} {direction}")
    
    return df

def create_visualizations(df):
    """Create comprehensive visualizations for the dataset"""
    
    print("\n" + "="*50)
    print("7. GENERATING VISUALIZATIONS")
    print("="*50)
    
    # Set up the plotting area
    fig = plt.figure(figsize=(20, 24))
    
    # 1. Equipment type distribution
    plt.subplot(4, 3, 1)
    equipment_counts = df['equipment_type'].value_counts()
    plt.pie(equipment_counts.values, labels=equipment_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title('Equipment Type Distribution', fontsize=12, fontweight='bold')
    
    # 2. Failure probability distribution
    plt.subplot(4, 3, 2)
    plt.hist(df['failure_probability'], bins=30, alpha=0.7, color='red', edgecolor='black')
    plt.xlabel('Failure Probability')
    plt.ylabel('Frequency')
    plt.title('Failure Probability Distribution', fontsize=12, fontweight='bold')
    plt.axvline(df['failure_probability'].mean(), color='darkred', linestyle='--', 
                label=f'Mean: {df["failure_probability"].mean():.3f}')
    plt.legend()
    
    # 3. Equipment age vs failure probability
    plt.subplot(4, 3, 3)
    for eq_type in df['equipment_type'].unique():
        eq_data = df[df['equipment_type'] == eq_type]
        plt.scatter(eq_data['age_months'], eq_data['failure_probability'], 
                   alpha=0.6, label=eq_type, s=30)
    plt.xlabel('Age (Months)')
    plt.ylabel('Failure Probability')
    plt.title('Age vs Failure Probability by Equipment Type', fontsize=12, fontweight='bold')
    plt.legend()
    
    # 4. Academic calendar impact
    plt.subplot(4, 3, 4)
    weekly_usage = df.groupby('week_of_year')['daily_usage_hours'].mean()
    plt.plot(weekly_usage.index, weekly_usage.values, linewidth=2, color='blue')
    plt.xlabel('Week of Year')
    plt.ylabel('Average Daily Usage (Hours)')
    plt.title('Equipment Usage Throughout Academic Year', fontsize=12, fontweight='bold')
    
    # Highlight exam periods
    exam_weeks = [15, 16, 35, 36]
    for week in exam_weeks:
        if week in weekly_usage.index:
            plt.axvline(week, color='red', linestyle='--', alpha=0.7)
    plt.text(15, weekly_usage.max() * 0.9, 'Exam Periods', color='red', fontweight='bold')
    
    # 5. Maintenance urgency by equipment type
    plt.subplot(4, 3, 5)
    urgency_pivot = pd.crosstab(df['equipment_type'], df['maintenance_urgency'], normalize='index') * 100
    urgency_pivot.plot(kind='bar', stacked=True, ax=plt.gca())
    plt.xlabel('Equipment Type')
    plt.ylabel('Percentage')
    plt.title('Maintenance Urgency Distribution by Equipment', fontsize=12, fontweight='bold')
    plt.legend(title='Urgency Level', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    
    # 6. Operating temperature vs failure probability
    plt.subplot(4, 3, 6)
    plt.scatter(df['operating_temperature'], df['failure_probability'], 
                alpha=0.6, c=df['degradation_score'], cmap='viridis', s=30)
    plt.xlabel('Operating Temperature (°C)')
    plt.ylabel('Failure Probability')
    plt.title('Temperature vs Failure Probability', fontsize=12, fontweight='bold')
    plt.colorbar(label='Degradation Score')
    
    # 7. Seasonal impact on equipment performance
    plt.subplot(4, 3, 7)
    seasonal_data = df.groupby('season').agg({
        'failure_probability': 'mean',
        'operating_temperature': 'mean',
        'dust_accumulation': 'mean'
    })
    
    x = range(len(seasonal_data.index))
    width = 0.25
    plt.bar([i - width for i in x], seasonal_data['failure_probability'] * 100, 
            width, label='Failure Prob (%)', alpha=0.8)
    plt.bar(x, seasonal_data['operating_temperature'], 
            width, label='Avg Temp (°C)', alpha=0.8)
    plt.bar([i + width for i in x], seasonal_data['dust_accumulation'], 
            width, label='Dust Level', alpha=0.8)
    
    plt.xlabel('Season')
    plt.ylabel('Value')
    plt.title('Seasonal Impact on Equipment Performance', fontsize=12, fontweight='bold')
    plt.xticks(x, seasonal_data.index)
    plt.legend()
    
    # 8. Days since last maintenance vs failure probability
    plt.subplot(4, 3, 8)
    plt.scatter(df['last_maintenance_days'], df['failure_probability'], 
                alpha=0.6, s=30, c='orange')
    plt.xlabel('Days Since Last Maintenance')
    plt.ylabel('Failure Probability')
    plt.title('Maintenance Gap vs Failure Risk', fontsize=12, fontweight='bold')
    
    # Add trend line
    z = np.polyfit(df['last_maintenance_days'], df['failure_probability'], 1)
    p = np.poly1d(z)
    plt.plot(df['last_maintenance_days'], p(df['last_maintenance_days']), "r--", alpha=0.8)
    
    # 9. Performance score distribution by equipment type
    plt.subplot(4, 3, 9)
    df.boxplot(column='performance_score', by='equipment_type', ax=plt.gca())
    plt.title('Performance Score Distribution by Equipment Type', fontsize=12, fontweight='bold')
    plt.suptitle('')  # Remove automatic title
    plt.xticks(rotation=45)
    
    # 10. Correlation heatmap
    plt.subplot(4, 3, 10)
    numeric_features = ['age_months', 'daily_usage_hours', 'degradation_score', 
                       'operating_temperature', 'performance_score', 'failure_probability']
    correlation_matrix = df[numeric_features].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0, 
                square=True, ax=plt.gca(), fmt='.2f')
    plt.title('Feature Correlation Matrix', fontsize=12, fontweight='bold')
    
    # 11. Usage hours distribution
    plt.subplot(4, 3, 11)
    df['daily_usage_hours'].hist(bins=25, alpha=0.7, color='green', edgecolor='black')
    plt.xlabel('Daily Usage Hours')
    plt.ylabel('Frequency')
    plt.title('Daily Usage Hours Distribution', fontsize=12, fontweight='bold')
    plt.axvline(df['daily_usage_hours'].mean(), color='darkgreen', linestyle='--',
                label=f'Mean: {df["daily_usage_hours"].mean():.1f}h')
    plt.legend()
    
    # 12. Degradation score by equipment age
    plt.subplot(4, 3, 12)
    for eq_type in df['equipment_type'].unique():
        eq_data = df[df['equipment_type'] == eq_type]
        plt.scatter(eq_data['age_months'], eq_data['degradation_score'], 
                   alpha=0.6, label=eq_type, s=30)
    plt.xlabel('Age (Months)')
    plt.ylabel('Degradation Score')
    plt.title('Equipment Degradation Over Time')